// Browser smoke test with deterministic OCR and PDF worker stubs.
import {chromium} from "playwright";
import {spawn} from "node:child_process";
import assert from "node:assert/strict";

const server=spawn("python3",["-m","http.server","8765","--bind","127.0.0.1","--directory","docs"],{stdio:"ignore"});
let browser;
try {
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({acceptDownloads:true,viewport:{width:1200,height:800}});
  const errors=[];
  page.on("pageerror",e=>errors.push(e.message));
  await page.route("**/tesseract.min.js",r=>r.fulfill({status:200,contentType:"application/javascript",body:
    "window.Tesseract={createWorker:async()=>({recognize:async()=>({data:{text:'Sample recognized text <img src=x onerror=alert(1)>'}}),terminate:async()=>{}})};"
  }));
  await page.route("**/pdf.min.js",r=>r.fulfill({status:200,contentType:"application/javascript",body:
    "window.pdfjsLib={GlobalWorkerOptions:{},getDocument:()=>({promise:Promise.resolve({numPages:2,getPage:async()=>({getViewport:({scale})=>({width:300*scale,height:400*scale}),render:()=>({promise:Promise.resolve()}),cleanup:()=>{}}),destroy:async()=>{}})})};"
  }));
  let opened=false;
  for(let attempt=0;attempt<15;attempt++) {
    try {await page.goto("http://127.0.0.1:8765/",{waitUntil:"load",timeout:2000});opened=true;break;}
    catch {await new Promise(resolve=>setTimeout(resolve,200));}
  }
  assert.ok(opened,"Local test site did not load");
  assert.match(await page.title(),/OpenOCR/);
  await page.locator("#file-input").setInputFiles({name:"scan.png",mimeType:"image/png",buffer:Buffer.from("89504e470d0a1a0a","hex")});
  assert.equal(await page.locator("#recognize").isDisabled(),false);
  await page.locator("#recognize").click();
  await page.waitForFunction(()=>document.querySelector("#status").textContent.includes("All done"));
  assert.match(await page.locator("#output").inputValue(),/Sample recognized text/);
  assert.equal(await page.locator("img").count(),0,"OCR data must remain plain text");
  await page.locator("#tab-json").click();
  const parsed=JSON.parse(await page.locator("#output").inputValue());
  assert.equal(parsed[0].source,"scan.png");
  assert.equal(parsed[0].text.includes("<img"),true);
  const downloadPromise=page.waitForEvent("download");
  await page.locator("#download-json").click();
  const download=await downloadPromise;
  assert.equal(download.suggestedFilename(),"scan_ocr.json");
  await page.locator("#clear").click();
  assert.equal(await page.locator("#recognize").isDisabled(),true);
  await page.locator("#file-input").setInputFiles({name:"report.pdf",mimeType:"application/pdf",buffer:Buffer.from("%PDF-1.4")});
  await page.locator("#recognize").click();
  await page.waitForFunction(()=>document.querySelector("#status").textContent.includes("All done"));
  await page.locator("#tab-json").click();
  const pdfResults=JSON.parse(await page.locator("#output").inputValue());
  assert.equal(pdfResults.length,2);
  assert.deepEqual(pdfResults.map(x=>x.page),[1,2]);
  await page.setViewportSize({width:375,height:800});
  assert.equal(await page.locator("#recognize").isVisible(),true);
  assert.deepEqual(errors,[]);
  console.log("Browser smoke test passed: upload, OCR, PDF pages, export, mobile layout.");
} finally {
  if(browser) await browser.close();
  server.kill();
}
