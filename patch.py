# v35 (10 ต.ค. 2569) — ป้าย "เพิ่งแก้พิกัด" + เลื่อนกลับไปที่งานเดิม + เตือน "พิกัดน่าสงสัย"
# ใช้: python3 patch.py <in index.html> <out index.html>   (แต่ละจุดต้องเจอครั้งเดียวพอดี)
import sys
src = open(sys.argv[1], encoding="utf-8").read()

def rep(old, new):
    global src
    n = src.count(old)
    assert n == 1, (n, old[:60])
    src = src.replace(old, new)

# 1) CSS
rep(".job .body{flex:1; min-width:0}",
    ".job .body{flex:1; min-width:0}\n"
    ".job.justfixed,.card.justfixed{background:var(--ok-soft); box-shadow:inset 5px 0 0 var(--ok)}\n"
    ".fixdone{display:inline-flex; margin-top:7px; padding:4px 10px; border-radius:999px; font-size:13px; font-weight:700; background:var(--ok); color:#fff; white-space:nowrap}\n"
    ".fixflag{display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-top:8px; padding:8px 10px; border-radius:10px; font-size:13.5px; font-weight:600; background:var(--warn-soft); color:var(--warn); border:1px solid var(--warn)}\n"
    ".fixflag button{font:inherit; font-size:12.5px; padding:3px 9px; border-radius:8px; border:1px solid var(--warn); background:transparent; color:var(--warn); cursor:pointer}\n"
    ".btn.suspfix{border-color:var(--warn); color:var(--warn); background:var(--warn-soft); font-weight:700}\n"
    ".tab .badge.warn{background:var(--warn)}")

# 2) โมดูลใหม่ วางก่อน jobList()
MOD = r'''/* =============== พิกัดน่าสงสัย + ป้าย "เพิ่งแก้พิกัด" (v35 · 10 ต.ค. 2569 — เจ้าของขอ) ===============
   Why: กดแก้พิกัดแล้วหน้าโหลดใหม่ จอเลื่อน ไม่รู้ว่าแก้ใบไหนไป · และต้องไล่เปิดดูเองว่าใบไหนพิกัดไม่ตรง
   1) แก้/ขอแก้แล้ว → จำ id ไว้ (sessionStorage ปิดแอปแล้วหาย) → การ์ดพื้นเขียว + ป้าย "✅ เพิ่งแก้พิกัด" + เลื่อนจอไปที่ใบนั้น
   2) ตรวจพิกัดน่าสงสัย (เฉพาะงานส่ง/รับสินค้าที่ปิดแล้ว · เจ้าของ+แอดมินเห็น) **แสดงผลอย่างเดียว ไม่แก้อะไรเอง**
      ก. มีพิกัดแค่ฝั่งเดียว (ไม่มีต้นทางหรือปลายทาง)
      ข. ต้นทางกับปลายทางห่างกันไม่ถึง 0.3 กม. (กดเริ่ม/ปิดงานที่เดียวกัน)
      ค. ระยะเส้นตรงต่างจากงานชื่อเดียวกันใบอื่น (≥2 ใบ ไม่มีจุดแวะ) เกิน 25% และเกิน 5 กม. — เทียบค่ามัธยฐาน
      กด "👍 พิกัดถูกแล้ว" = ไม่เตือนใบนี้อีก (จำในเครื่องนี้ · ถ้าพิกัดเปลี่ยนจะตรวจใหม่) */
var FIXMARK=null;
try{ FIXMARK=JSON.parse(sessionStorage.getItem("rc.fixMark")||"null"); }catch(e){ FIXMARK=null; }
function fixMarkSet(id, applied){
  FIXMARK={id:id, at:Date.now(), applied:!!applied};
  try{ sessionStorage.setItem("rc.fixMark", JSON.stringify(FIXMARK)); }catch(e){}
}
function fixMarkOn(j){ return !!(FIXMARK && j && FIXMARK.id===j.id); }
function fixMarkText(){
  var d=new Date(FIXMARK.at), hm=pad(d.getHours())+":"+pad(d.getMinutes());
  return (FIXMARK.applied ? "✅ เพิ่งแก้พิกัด " : "📨 เพิ่งส่งคำขอแก้พิกัด ")+hm;
}
/* เลื่อนจอไปที่การ์ดที่เพิ่งแก้ (หลังโหลดข้อมูลใหม่ ลำดับ/ความสูงการ์ดเปลี่ยน จึงเลื่อนตามตำแหน่งการ์ด ไม่ใช่ตำแหน่งจอเดิม) */
function fixMarkFocus(){
  if(!FIXMARK) return;
  var els=document.querySelectorAll('[data-job="'+FIXMARK.id+'"]');
  for(var i=0;i<els.length;i++){
    if(els[i].offsetParent){ els[i].scrollIntoView({block:"center"}); return; }
  }
}
function fixOkMap(){ try{ return JSON.parse(localStorage.getItem("rc.fixOk")||"{}")||{}; }catch(e){ return {}; } }
function fixSig(j){
  function p(x){ return (x&&x.lat!=null) ? (+x.lat).toFixed(4)+","+(+x.lng).toFixed(4) : "-"; }
  return p(j.start)+"|"+p(j.end)+"|"+stopsOf(j).length;
}
function fixOkSet(j){
  var m=fixOkMap(); m[j.id]=fixSig(j);
  try{ localStorage.setItem("rc.fixOk", JSON.stringify(m)); }catch(e){}
}
var SUSP_TYPES={"ส่งสินค้า":1, "รับสินค้า":1};
function median(a){ var b=a.slice().sort(function(x,y){return x-y;}), n=b.length; return n ? (n%2 ? b[(n-1)/2] : (b[n/2-1]+b[n/2])/2) : 0; }
function hasPin(p){ return !!(p && p.lat!=null && p.lng!=null); }
/* คืน {id: ข้อความ} ของงานที่พิกัดน่าสงสัย */
function suspectAll(){
  var out={}, ok=fixOkMap(), by={};
  DB.job.forEach(function(j){
    if(j.status!=="done" || !SUSP_TYPES[j.type] || !(j.km>0) || stopsOf(j).length) return;
    var k=j.type+"|"+(j.label||"").trim();
    if(!(j.label||"").trim()) return;
    (by[k]=by[k]||[]).push(j);
  });
  DB.job.forEach(function(j){
    if(j.status!=="done" || !SUSP_TYPES[j.type] || fixPending(j)) return;
    if(ok[j.id] && ok[j.id]===fixSig(j)) return;
    var s=hasPin(j.start), e=hasPin(j.end);
    if(!s && !e) return;                       /* ไม่มีพิกัดเลย = งานคีย์มือ/นำเข้า ไม่ใช่เรื่องกดผิดที่ */
    if(!e){ out[j.id]="ไม่มีพิกัดปลายทาง"; return; }
    if(!s){ out[j.id]="ไม่มีพิกัดต้นทาง"; return; }
    if(!stopsOf(j).length && haversine(j.start, j.end)<0.3){
      out[j.id]="ต้นทางกับปลายทางเป็นจุดเดียวกัน (น่าจะกดปิดงานที่ต้นทาง)"; return;
    }
    if(stopsOf(j).length || !(j.km>0) || !(j.label||"").trim()) return;
    var others=(by[j.type+"|"+j.label.trim()]||[]).filter(function(o){ return o.id!==j.id; });
    if(others.length<2) return;
    var m=median(others.map(function(o){ return o.km; })), d=Math.abs(j.km-m);
    if(d>=5 && d>=0.25*m){
      out[j.id]="ระยะเส้นตรง "+j.km.toFixed(1)+" กม. แต่งานชื่อเดียวกันอีก "+others.length+" ใบ ปกติ ~"+m.toFixed(1)+" กม. ("+(j.km>m?"ไกลกว่า ":"ใกล้กว่า ")+d.toFixed(1)+" กม.)";
    }
  });
  return out;
}
function suspectCount(filter){
  var S=suspectAll(), n=0;
  DB.job.forEach(function(j){ if(S[j.id] && (!filter || filter(j))) n++; });
  return n;
}
/* ป้ายบนการ์ด: เพิ่งแก้ (เขียว) / น่าสงสัย (เหลือง) — host = ส่วนเนื้อการ์ด, card = ตัวการ์ดทั้งใบ */
function fixBadges(j, host, card, S){
  card.setAttribute("data-job", j.id);
  if(fixMarkOn(j)){
    card.classList.add("justfixed");
    var ok=document.createElement("div"); ok.className="fixdone"; ok.textContent=fixMarkText();
    host.appendChild(ok);
  }
  var msg=S && S[j.id];
  if(msg){
    var w=document.createElement("div"); w.className="fixflag";
    var t=document.createElement("span"); t.textContent="⚠️ พิกัดน่าสงสัย — "+msg; w.appendChild(t);
    var b=document.createElement("button"); b.type="button"; b.textContent="👍 พิกัดถูกแล้ว";
    b.title="ไม่ต้องเตือนใบนี้อีก (ถ้าพิกัดเปลี่ยนจะตรวจใหม่)";
    b.onclick=function(){ fixOkSet(j); toast("รับทราบ ไม่เตือนใบนี้อีก"); buildTabs(); render(); };
    w.appendChild(b);
    host.appendChild(w);
  }
  return !!msg;
}
var SUSP_ONLY=false;
'''
rep("function jobList(host,list,showEmp){",
    MOD + "function jobList(host,list,showEmp){")

# 3) jobList: คำนวณครั้งเดียวต่อรายการ + ติดป้ายบนการ์ด + ปุ่มแก้พิกัดเด่นขึ้นเมื่อน่าสงสัย
rep("""  if(!list.length){ host.innerHTML='<div class="pad hint">ยังไม่มีรายการ</div>'; return; }
  list.forEach(function(j){
    var row=document.createElement("div"); row.className="job";""",
"""  if(!list.length){ host.innerHTML='<div class="pad hint">ยังไม่มีรายการ</div>'; return; }
  var SUS=isStaff(me) ? suspectAll() : {};
  list.forEach(function(j){
    var row=document.createElement("div"); row.className="job";""")
rep("""      (j.note?'<div class="hint">'+esc(j.note)+'</div>':'');
    var amt=document.createElement("div");""",
"""      (j.note?'<div class="hint">'+esc(j.note)+'</div>':'');
    var isSus=fixBadges(j, body, row, SUS);
    var amt=document.createElement("div");""")
rep("""      fb.className="btn sm ghost"; fb.textContent="📍 "+(isOwner(me)?"แก้พิกัด":"ขอแก้พิกัด");
      side.appendChild(fb);""",
"""      fb.className="btn sm ghost"+(isSus?" suspfix":""); fb.textContent="📍 "+(isOwner(me)?"แก้พิกัด":"ขอแก้พิกัด");
      side.appendChild(fb);""")

# 4) หลังแก้/ขอแก้: จำ id แล้วเลื่อนจอไปที่การ์ดนั้น
rep("""        if(r.applied){ return bootstrap().then(function(){ render(); }); }   /* เจ้าของแก้เอง — ดึงค่าใหม่มาโชว์ */
        DB.fixOpen=DB.fixOpen||{};
        DB.fixOpen[j.id]={job_id:j.id, which:wSel.value, place:(p.place ? p.name : "จุดที่ยังไม่มีชื่อ")};
        render();""",
"""        fixMarkSet(j.id, !!r.applied);
        if(r.applied){ return bootstrap().then(function(){ buildTabs(); render(); fixMarkFocus(); }); }   /* เจ้าของแก้เอง — ดึงค่าใหม่มาโชว์ */
        DB.fixOpen=DB.fixOpen||{};
        DB.fixOpen[j.id]={job_id:j.id, which:wSel.value, place:(p.place ? p.name : "จุดที่ยังไม่มีชื่อ")};
        render(); fixMarkFocus();""")

# 5) หน้า "รอใส่ราคา": ป้ายเดียวกัน
rep("""  if(!list.length){ host.innerHTML='<div class="card pad hint">ไม่มีงานค้าง — ทุกงานมีค่าเที่ยวครบแล้ว</div>'; return; }
  list.forEach(function(j){
    var c=document.createElement("div"); c.className="card pad stack"; c.style.marginBottom="12px";""",
"""  if(!list.length){ host.innerHTML='<div class="card pad hint">ไม่มีงานค้าง — ทุกงานมีค่าเที่ยวครบแล้ว</div>'; return; }
  var SUS=suspectAll();
  list.forEach(function(j){
    var c=document.createElement("div"); c.className="card pad stack"; c.style.marginBottom="12px";""")
rep("""      '</div>' + (j.note?'<div class="hint">'+esc(j.note)+'</div>':'');
    c.appendChild(head);""",
"""      '</div>' + (j.note?'<div class="hint">'+esc(j.note)+'</div>':'');
    var isSus=fixBadges(j, head, c, SUS);
    c.appendChild(head);""")
rep("""        fbtn.textContent="📍 "+(isOwner(me)?"แก้พิกัด":"ขอแก้พิกัด");
        fbtn.onclick=function(){
          if(!fpan.classList.contains("hidden")){ fpan.classList.add("hidden"); fpan.innerHTML=""; return; }""",
"""        fbtn.textContent="📍 "+(isOwner(me)?"แก้พิกัด":"ขอแก้พิกัด");
        if(isSus) fbtn.className+=" suspfix";
        fbtn.onclick=function(){
          if(!fpan.classList.contains("hidden")){ fpan.classList.add("hidden"); fpan.innerHTML=""; return; }""")

# 6) หน้า "งานทั้งหมด": แถบสรุป + ปุ่มดูเฉพาะงานน่าสงสัย
rep("""  var e=$("flEmp").value, t=$("flTruck").value, ty=$("flType").value, m=$("flMonth").value;
  jobList($("allJobs"), sorted(DB.job.filter(function(j){
    return (!e||j.emp===e)&&(!t||j.truck===t)&&(!ty||j.type===ty)&&(!m||ym(j.date)===m);
  })), true);""",
"""  var e=$("flEmp").value, t=$("flTruck").value, ty=$("flType").value, m=$("flMonth").value;
  function pass(j){ return (!e||j.emp===e)&&(!t||j.truck===t)&&(!ty||j.type===ty)&&(!m||ym(j.date)===m); }
  var bar=$("suspBar");
  if(!bar){
    bar=document.createElement("div"); bar.id="suspBar"; bar.className="fixflag";
    bar.style.cssText="margin-top:12px; justify-content:space-between";
    $("allJobs").parentNode.insertBefore(bar, $("allJobs"));
  }
  var S=isStaff(me) ? suspectAll() : {}, ns=0;
  DB.job.forEach(function(j){ if(S[j.id] && pass(j)) ns++; });
  if(!ns) SUSP_ONLY=false;
  bar.classList.toggle("hidden", !ns);
  bar.innerHTML='<span>⚠️ พิกัดน่าสงสัย '+ns+' งาน'+(SUSP_ONLY?' — กำลังแสดงเฉพาะงานเหล่านี้':' — ควรเปิดดูและแก้')+'</span>'+
    '<button type="button" id="suspTog">'+(SUSP_ONLY?'ดูทุกงาน':'ดูเฉพาะงานนี้')+'</button>';
  if(ns) $("suspTog").onclick=function(){ SUSP_ONLY=!SUSP_ONLY; renderJobs(); };
  jobList($("allJobs"), sorted(DB.job.filter(function(j){
    return pass(j) && (!SUSP_ONLY || S[j.id]);
  })), true);""")

# 7) ตัวเลขเตือนบนแท็บ "งานทั้งหมด"
rep("""    if(t[0]==="wait"){
      var n=waiting().length;
      if(n){ var s=document.createElement("span"); s.className="badge"; s.textContent=n; b.appendChild(s); }
    }""",
"""    if(t[0]==="wait"){
      var n=waiting().length;
      if(n){ var s=document.createElement("span"); s.className="badge"; s.textContent=n; b.appendChild(s); }
    }
    if(t[0]==="jobs" && isStaff(me)){
      var ns=suspectCount();
      if(ns){ var w=document.createElement("span"); w.className="badge warn"; w.textContent="⚠️"+ns; w.title="พิกัดน่าสงสัย "+ns+" งาน"; b.appendChild(w); }
    }""")

open(sys.argv[2], "w", encoding="utf-8").write(src)
print("ok", len(src))
