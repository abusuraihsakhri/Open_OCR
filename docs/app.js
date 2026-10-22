import {validateFiles,extension,markdownFor,jsonFor,filenameSafe,MAX_PAGES} from "./ocr-utils.mjs";
const el = id => document.getElementById(id);
const drop = el("drop-zone"), fileInput = el("file-input"), output = el("output");
let files = [], results = [], view = "markdown", processing = false;
function status(message, kind = "") {
  el("status").textContent = message;
  el("status-dot").className = "dot" + (kind ? " " + kind : "");
}
function controls() {
  el("recognize").disabled = processing || files.length === 0;
  el("clear").disabled = processing;
  fileInput.disabled = processing;
  el("language").disabled = processing;
  for (const id of ["copy","download-md","download-json"]) el(id).disabled = processing || results.length === 0;
  drop.setAttribute("aria-disabled", String(processing));
}
function selected() {
  const list = el("file-list");
  list.replaceChildren();
  for (const f of files) {
    const li = document.createElement("li"), name = document.createElement("span"), size = document.createElement("span");
    name.textContent = f.name;
    size.textContent = (f.size / 1048576).toFixed(1) + " MB";
    li.append(name,size);
    list.appendChild(li);
  }
  controls();
}
function render() {
  output.value = view === "markdown" ? markdownFor(results) : jsonFor(results);
  el("result-count").textContent = results.length + (results.length === 1 ? " page" : " pages");
  for (const format of ["markdown","json"]) {
    const tab = el("tab-"+format), active = view === format;
    tab.classList.toggle("active",active);
    tab.setAttribute("aria-selected",String(active));
  }
  controls();
}
function addFiles(incoming) {
  if (processing) return;
  const next = validateFiles(Array.from(incoming), files);
  files = next.selected; selected();
  status(next.errors.length ? next.errors.join(" ") : files.length + " file(s) selected.", next.errors.length ? "error" : "ready");
}
fileInput.addEventListener("change",e=>{addFiles(e.target.files);fileInput.value="";});
drop.addEventListener("keydown",e=>{
  if (!processing && (e.key==="Enter" || e.key===" ")) {e.preventDefault();fileInput.click();}
});
for (const event of ["dragover","dragenter"]) drop.addEventListener(event,e=>{e.preventDefault();if(!processing)drop.classList.add("dragover");});
for (const event of ["dragleave","drop"]) drop.addEventListener(event,e=>{e.preventDefault();drop.classList.remove("dragover");});
drop.addEventListener("drop",e=>addFiles(e.dataTransfer.files));
el("clear").addEventListener("click",()=>{
  if(processing)return;
  files=[];results=[];el("progress").value=0;selected();render();status("Select a document to begin.");
});
el("tab-markdown").addEventListener("click",()=>{view="markdown";render();});
el("tab-json").addEventListener("click",()=>{view="json";render();});
el("copy").addEventListener("click",async()=>{
  try {await navigator.clipboard.writeText(output.value);status("Copied text.", "ready");}
  catch {output.focus();output.select();status("Clipboard unavailable. Select and copy the highlighted text.", "error");}
});
function save(text, extensionName, mime) {
  const name = files.length === 1 ? files[0].name.replace(/\.[^.]+$/,"") : "batch";
  const url = URL.createObjectURL(new Blob([text],{type:mime}));
  const a = document.createElement("a");
  a.href = url;a.download=filenameSafe(name)+"_ocr."+extensionName;
  document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
el("download-md").addEventListener("click",()=>save(markdownFor(results),"md","text/markdown;charset=utf-8"));
el("download-json").addEventListener("click",()=>save(jsonFor(results),"json","application/json;charset=utf-8"));
async function extract(worker, image, source, page, percent) {
  status("Recognizing " + source + (page ? ", page " + page : "") + "…");
  const recognized = await worker.recognize(image);
  const text = (recognized.data && recognized.data.text || "").trim();
  results.push({source,page,text});
  render();
  el("progress").value=Math.min(99,Math.round(percent));
}
async function pdfPages(worker, file, index, count) {
  if (!window.pdfjsLib) throw Error("PDF.js failed to load; check your network and retry.");
  const buffer = await file.arrayBuffer();
  const task = window.pdfjsLib.getDocument({data:new Uint8Array(buffer),isEvalSupported:false});
  const pdf = await task.promise;
  try {
    if (pdf.numPages > MAX_PAGES) throw Error(file.name + " exceeds the 50-page PDF limit.");
    for (let n=1;n<=pdf.numPages;n++) {
      const page = await pdf.getPage(n);
      const original = page.getViewport({scale:1});
      const scale = Math.min(2, Math.sqrt(5000000/(original.width*original.height)));
      const viewport = page.getViewport({scale});
      const canvas = document.createElement("canvas");
      canvas.width=Math.max(1,Math.ceil(viewport.width));
      canvas.height=Math.max(1,Math.ceil(viewport.height));
      try {
        await page.render({canvasContext:canvas.getContext("2d"),viewport}).promise;
        await extract(worker,canvas,file.name,n,100*(index+n/pdf.numPages)/count);
      } finally {
        canvas.width=0;canvas.height=0;page.cleanup();
      }
    }
  } finally {await pdf.destroy();}
}
async function run() {
  if (processing || files.length===0) return;
  if (!window.Tesseract) {status("Tesseract.js failed to load. Check your network and reload.","error");return;}
  processing=true;results=[];render();el("progress").value=0;
  let worker=null;
  try {
    status("Loading OCR engine and language data…");
    if(window.pdfjsLib) window.pdfjsLib.GlobalWorkerOptions.workerSrc="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
    worker=await window.Tesseract.createWorker(el("language").value,1,{logger:m=>{
      if (m.status==="recognizing text" && typeof m.progress==="number") status("Recognizing text… "+Math.round(m.progress*100)+"%");
    }});
    for (let i=0;i<files.length;i++) {
      const file=files[i];
      if (extension(file.name)==="pdf") await pdfPages(worker,file,i,files.length);
      else await extract(worker,file,file.name,null,100*(i+1)/files.length);
    }
    el("progress").value=100;
    status("Complete: "+results.length+" page(s) recognized.","ready");
  } catch(e) {
    console.error("OCR error:",e);
    status("OCR failed: "+(e && e.message ? e.message : String(e)),"error");
  } finally {
    if(worker) {try {await worker.terminate();}catch(e){console.error("Worker cleanup error:",e);}}
    processing=false;controls();
  }
}
el("recognize").addEventListener("click",run);
render();selected();
