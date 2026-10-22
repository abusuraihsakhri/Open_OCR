import test from "node:test";
import assert from "node:assert/strict";
import {validateFiles,markdownFor,jsonFor,extension,filenameSafe,MAX_FILES} from "../docs/ocr-utils.mjs";
const file=(name,size=100,lastModified=1)=>({name,size,lastModified});
test("validates file sizes and extensions",()=>{
  const r=validateFiles([file("scan.PNG"),file("paper.pdf"),file("evil.exe"),file("empty.jpg",0),file("big.png",26e6)]);
  assert.equal(r.selected.length,2);
  assert.equal(r.errors.length,3);
  assert.equal(extension("ABC.PDF"),"pdf");
});
test("deduplicates and limits batches",()=>{
  assert.equal(validateFiles([file("test.png"),file("test.png")]).selected.length,1);
  const files=Array.from({length:MAX_FILES+2},(_,i)=>file(i+".png"));
  assert.equal(validateFiles(files).selected.length,MAX_FILES);
});
test("exports valid JSON and multi-page Markdown",()=>{
  const r=[{source:"a.pdf",page:1,text:"A"},{source:"a.pdf",page:2,text:"B"}];
  assert.deepEqual(JSON.parse(jsonFor(r)),r);
  assert.match(markdownFor(r),/Page 1/);
  assert.match(markdownFor(r),/Page 2/);
  assert.match(markdownFor(r),/---/);
});
test("does not process OCR text as markup",()=>{
  const unsafe="<img src=x onerror=alert(1)>";
  assert.equal(JSON.parse(jsonFor([{source:"x.png",page:null,text:unsafe}]))[0].text,unsafe);
  assert.equal(filenameSafe("../hello world?"),"hello_world");
});
