// Real browser OCR integration test using production CDN assets and language files.
import {chromium} from "playwright";
import {spawn} from "node:child_process";
import assert from "node:assert/strict";

const server=spawn("python3",["-m","http.server","8766","--bind","127.0.0.1","--directory","docs"],{stdio:"ignore"});
let browser;
try {
  browser=await chromium.launch({headless:true});
  const page=await browser.newPage({viewport:{width:1100,height:800}});
  const errors=[];
  page.on("pageerror",error=>errors.push(error.message));
  let connected=false;
  for(let n=0;n<20;n++){
    try {await page.goto("http://127.0.0.1:8766/",{waitUntil:"load",timeout:30000});connected=true;break;}
    catch(e){await new Promise(resolve=>setTimeout(resolve,300));}
  }
  assert.ok(connected,"Cannot load browser OCR application.");
  await page.waitForFunction(()=>Boolean(window.Tesseract&&window.pdfjsLib),null,{timeout:60000});
  const bytes=await page.evaluate(async()=>{
    const canvas=document.createElement("canvas");
    canvas.width=780;canvas.height=175;
    const context=canvas.getContext("2d");
    context.fillStyle="#fff";context.fillRect(0,0,780,175);
    context.fillStyle="#000";context.font="bold 70px Arial";
    context.fillText("HELLO OCR 123",20,115);
    const blob=await new Promise(resolve=>canvas.toBlob(resolve,"image/png"));
    return Array.from(new Uint8Array(await blob.arrayBuffer()));
  });
  await page.locator("#file-input").setInputFiles({name:"hello.png",mimeType:"image/png",buffer:Buffer.from(bytes)});
  await page.locator("#recognize").click();
  await page.waitForFunction(()=>document.querySelector("#status").textContent.startsWith("All done"),null,{timeout:150000});
  let output=await page.locator("#output").inputValue();
  assert.match(output,/HELLO/i,"Real Tesseract OCR missed the sample image: "+output);
  console.log("Real image OCR recognized:",output.replace(/\s+/g," ").slice(0,160));
  await page.locator("#clear").click();
  const paper=await browser.newPage();
  await paper.setContent('<main style="font:bold 56px Arial;color:black;background:white;padding:35px">HELLO PDF OCR</main>');
  const pdf=await paper.pdf({width:"800px",height:"300px",printBackground:true});
  await paper.close();
  await page.locator("#file-input").setInputFiles({name:"hello.pdf",mimeType:"application/pdf",buffer:pdf});
  await page.locator("#recognize").click();
  await page.waitForFunction(()=>document.querySelector("#status").textContent.startsWith("All done"),null,{timeout:150000});
  output=await page.locator("#output").inputValue();
  assert.match(output,/HELLO/i,"Real PDF OCR missed the sample PDF: "+output);
  console.log("Real PDF OCR recognized:",output.replace(/\s+/g," ").slice(0,160));
  assert.deepEqual(errors,[]);
} finally {
  if(browser) await browser.close();
  server.kill();
}
