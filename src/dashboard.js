"use strict";
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const full = n => n == null ? "—" : Number(n).toLocaleString("en-US",{maximumFractionDigits:1});
const fmt = n => n == null ? "—" : n >= 1e6 ? (n/1e6).toFixed(1)+"M" : n >= 1e4 ? (n/1e3).toFixed(1)+"K" : full(n);
const date = s => new Intl.DateTimeFormat("en-US",{month:"short",day:"numeric",timeZone:"UTC"}).format(new Date(s.slice(0,10)+"T00:00:00Z"));
const span = (a,b) => `${date(a)}–${date(b)}`;
const shift = (s,n) => {const d=new Date(s+"T00:00:00Z");d.setUTCDate(d.getUTCDate()+n);return d.toISOString().slice(0,10)};
const sum = (rows,key) => {const values=rows.map(r=>r[key]).filter(v=>v!=null);return values.length?values.reduce((a,b)=>a+b,0):rows.length?null:0};
const PLATS = D.platforms;
const byId = Object.fromEntries(PLATS.map(p=>[p.id,p]));
const weeks = D.weeks;
const records = p => p.records.filter(r=>r.date);
const weekRows = (p,w,c="All formats") => records(p).filter(r=>r.week_start===w&&(c==="All formats"||r.category===c));
const weekData = (p,w) => p.weekly.find(r=>r.start===w);
const covered = r => !!r && r.available!==false && r.value!=null;
const unit = p => p.id==="podcast"?"downloads":"views";
const coveredEnd = (p,row) => row.end > p.cutoff ? p.cutoff : row.end;
const contentUnit = p => p.id==="podcast"?"episodes":"posts";
const cats = p => [...new Set(records(p).map(r=>r.category))];
const colors = ["#a51d2d","#2166ac","#2a9d8f","#d97706","#7c3aed"];
const categoryColor = (p,c) => c==="All formats"?"var(--ink)":colors[cats(p).indexOf(c)%colors.length];
const safeUrl = u => /^https:\/\/(www\.)?(youtube\.com|instagram\.com)\//.test(u||"")?u:null;
const titleLink = r => safeUrl(r.url)?`<a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.title)}</a>`:esc(r.title);
const state = Object.fromEntries(PLATS.map(p=>[p.id,{metric:"value",hidden:new Set(),point:null,spark:null}]));
const audienceKey = p => p.id==="instagram"?"follows":p.id==="youtube"?"subscribers_gained":null;
const metricLabel = (p,m) => m==="value"?unit(p):m==="posts"?contentUnit(p):m==="follows"?"followers gained":m==="subscribers_gained"?"subscribers gained":"engagements";
const audienceNote = p => p.id==="instagram"?"Follows attributed to the 29 exported posts, including shared source-account posts. This is not the account’s current follower total.":"Known subscribers gained from exported videos. One dated video has no value. This is not the channel’s current subscriber total.";
const latestComplete = p => p.weekly.filter(r=>covered(r)&&!r.partial&&r.end<=p.cutoff).at(-1);
const cutoffText = p => `${p.id==="youtube"?"Export dated":"Snapshot"} ${date(p.cutoff)}, 2026`;
const status = (p,w) => {const r=weekData(p,w);return !covered(r)?"Unavailable":r.partial?"Partial week":"Covered week"};
const primary = (p,w,c,m) => {const r=weekData(p,w);if(!covered(r))return null;const rows=weekRows(p,w,c);return m==="posts"?rows.length:sum(rows,m)};
const dot = p => `<span class="dot" style="--platform:${p.color}"></span>`;

$("updateDate").textContent = date(D.updated)+", 2026";
$("coverageBanner").textContent = PLATS.map(p=>`${p.label}: ${date(p.cutoff)} ${p.id==="youtube"?"export":"snapshot"}${p.refresh_pending?"; update pending":""}`).join(". ")+". YouTube’s selected analytics date range is not included in its CSVs.";
const yt=byId.youtube, ig=byId.instagram, podcast=byId.podcast;
$("hero").innerHTML = [
 ["YouTube views",yt.totals.weekly_value??sum(records(yt),"value"),`${yt.totals.dated_posts} dated videos · ${date(yt.cutoff)} export`],
 ["Instagram views",ig.totals.value,`${ig.totals.posts} posts · ${date(ig.cutoff)} snapshot`],
 ["Podcast downloads",podcast.totals.value,`All players · ${podcast.totals.posts} episodes · ${date(podcast.cutoff)} snapshot`],
 ["Instagram followers gained",sum(records(ig),"follows"),"Attributed to 29 exported posts"],
 ["YouTube subscribers gained",sum(records(yt),"subscribers_gained"),"Known video gains · 1 value missing"],
].map(([label,value,detail])=>`<div class="card tile"><div class="label">${label}</div><div class="value">${fmt(value)}</div><div class="detail">${detail}</div></div>`).join("");

function platformCard(p){
 const available=p.weekly.filter(covered).slice(-8);
 const selected=state[p.id].spark||latestComplete(p)?.start||available.at(-1)?.start;
 state[p.id].spark=selected;
 const row=available.find(r=>r.start===selected)||weekData(p,selected);
 const max=Math.max(1,...available.map(r=>r.value));
 const bars=available.map((r,i)=>{const h=Math.max(1,32*r.value/max),label=`${p.label}, ${span(r.start,coveredEnd(p,r))}, ${full(r.value)} ${unit(p)}, ${status(p,r.start)}`;return `<g role="button" tabindex="0" class="spark-bar ${r.start===selected?"selected":""}" data-spark="${p.id}" data-week="${r.start}" aria-pressed="${r.start===selected}" aria-label="${esc(label)}"><rect class="spark-hit" x="${i*20}" y="0" width="20" height="38"/><rect class="spark-fill ${r.partial?"partial":""}" x="${i*20+2}" y="${36-h}" width="14" height="${h}" rx="2" fill="${p.color}" opacity=".48"/><title>${esc(label)}</title></g>`}).join("");
 return `<article class="card tile platform-card" style="--platform:${p.color}" id="platform-${p.id}"><div class="label">${dot(p)}${p.label}</div><div class="platform-metrics${audienceKey(p)?" paired":""}"><div class="value">${fmt(row?.value)} <span class="value-unit">${unit(p)}</span></div>${audienceKey(p)?`<div class="value audience-value">${fmt(primary(p,selected,"All formats",audienceKey(p)))} <span class="value-unit">${metricLabel(p,audienceKey(p))}</span></div>`:""}</div><div class="detail">${span(row.start,coveredEnd(p,row))} · ${row.posts} ${contentUnit(p)}</div><div class="spark-help">Select a week for exact stats.</div><svg class="spark" viewBox="0 0 160 38" preserveAspectRatio="none" aria-label="${p.label} weekly trend">${bars}</svg><div class="spark-range"><span>${date(available[0].start)}</span><span>${date(coveredEnd(p,available.at(-1)))}${available.at(-1).partial?" · partial":""}</span></div><div class="spark-readout" aria-live="polite"><strong>${span(row.start,coveredEnd(p,row))}, 2026</strong>${full(row.value)} ${unit(p)}${audienceKey(p)?` · ${full(primary(p,selected,"All formats",audienceKey(p)))} ${metricLabel(p,audienceKey(p))}`:""} · ${row.posts} ${contentUnit(p)} · ${status(p,row.start)}</div><div class="freshness">${cutoffText(p)}${p.refresh_pending?" · update pending":""}</div></article>`;
}
function renderPlatforms(){
 $("platforms").innerHTML=PLATS.map(platformCard).join("");
 $("platforms").querySelectorAll("[data-spark]").forEach(b=>{const activate=()=>{state[b.dataset.spark].spark=b.dataset.week;renderPlatforms();document.querySelector(`[data-spark="${b.dataset.spark}"][data-week="${b.dataset.week}"]`)?.focus({preventScroll:true})};b.onclick=activate;b.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();activate()}}});
}

function detail(p){
 const s=state[p.id],point=s.point;
 if(!point||s.hidden.has(point.category))return `<div class="point-help">Select a point—including a spike—to see its leading ${contentUnit(p)}. Use arrow keys to move between points and Enter to select.</div>`;
 const rows=weekRows(p,point.week,point.category),row=weekData(p,point.week),metric=s.metric==="posts"?"value":s.metric;
 const ranked=rows.filter(r=>r[metric]!=null).sort((a,b)=>b[metric]-a[metric]||a.title.localeCompare(b.title)).slice(0,3);
 const total=primary(p,point.week,point.category,s.metric);
 return `<div class="point-detail" role="region" aria-label="${p.label} selected point details" aria-live="polite"><div class="point-detail-head"><div><div class="point-detail-kicker">Content behind this point · ${status(p,point.week)}</div><strong class="point-detail-title">${esc(point.category)} · ${span(row.start,coveredEnd(p,row))}, 2026</strong></div><div class="point-actions"><div class="point-total">${full(total)} ${metricLabel(p,s.metric)}</div><button class="point-close" data-close="${p.id}">Close details</button></div></div><div class="point-detail-note">Top contributors by ${metricLabel(p,metric)}. Values belong to content published during this week.</div>${ranked.length?`<div class="point-posts">${ranked.map((r,i)=>`<article class="point-post"><div class="point-rank">${i+1}</div><div><div class="point-post-title">${titleLink(r)}</div><div class="point-post-meta">${date(r.date)}, 2026 · ${esc(r.category)}</div>${safeUrl(r.url)?`<a class="point-post-open" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">Open ${p.id==="youtube"?"video":"post"} ↗</a>`:""}</div><div class="point-post-stats"><strong>${full(r[metric])} ${metricLabel(p,metric)}</strong>${metric!=="value"?`<br>${full(r.value)} ${unit(p)}`:p.id==="podcast"&&r.downloads_first_30_days!=null?`<br>${full(r.downloads_first_30_days)} downloads in first 30 days`:r.engagements!=null?`<br>${full(r.engagements)} engagements`:""}</div></article>`).join("")}</div>`:`<div class="empty">No ${contentUnit(p)} in this series for this week.</div>`}</div>`;
}

function chart(p){
 const s=state[p.id],ww=p.weekly.filter(covered),names=["All formats",...cats(p)],visible=names.filter(c=>!s.hidden.has(c));
 const W=Math.max(920,ww.length*48+90),H=340,L=72,R=24,T=22,B=70;
 const values=visible.flatMap(c=>ww.map(w=>primary(p,w.start,c,s.metric))).filter(v=>v!=null);
 const high=Math.max(1,...values),pow=10**Math.floor(Math.log10(high/4)),raw=high/4/pow,step=(raw<=1?1:raw<=2?2:raw<=5?5:10)*pow,max=Math.ceil(high/step)*step;
 const x=i=>L+(ww.length===1?(W-L-R)/2:i*(W-L-R)/(ww.length-1)),y=v=>T+(H-B-T)*(1-v/max);
 const grid=Array.from({length:Math.round(max/step)+1},(_,i)=>`<line x1="${L}" x2="${W-R}" y1="${y(i*step)}" y2="${y(i*step)}" stroke="var(--grid)"/><text x="${L-12}" y="${y(i*step)+4}" text-anchor="end" fill="var(--muted)" font-size="11">${fmt(i*step)}</text>`).join("");
 const labels=ww.map((w,i)=>`<text transform="translate(${x(i)} ${H-B+19}) rotate(-50)" text-anchor="end" fill="var(--muted)" font-size="10">${date(w.start)}</text>`).join("");
 const lines=[...visible].reverse().map(c=>{const series=ww.map(w=>primary(p,w.start,c,s.metric)),color=categoryColor(p,c),total=c==="All formats";let paths=[],current=[];series.forEach((v,i)=>{if(v==null){if(current.length)paths.push(current.join(" "));current=[]}else current.push(`${x(i)},${y(v)}`)});if(current.length)paths.push(current.join(" "));
 const poly=paths.map(points=>`<polyline points="${points}" fill="none" stroke="${color}" stroke-width="${total?3.5:2.25}" ${total?'stroke-dasharray="8 4"':""} stroke-linejoin="round"/>`).join("");
 const marks=series.map((v,i)=>{if(v==null)return "";const selected=s.point?.week===ww[i].start&&s.point?.category===c,label=`${p.label}, ${c}, ${span(ww[i].start,coveredEnd(p,ww[i]))}, ${full(v)} ${metricLabel(p,s.metric)}. Show contributors.`;return `<g class="chart-point ${selected?"selected":""}" role="button" tabindex="${i===0?0:-1}" data-platform="${p.id}" data-category="${esc(c)}" data-week="${ww[i].start}" data-index="${i}" aria-pressed="${selected}" aria-label="${esc(label)}"><title>${esc(label)}</title><circle class="point-hit" cx="${x(i)}" cy="${y(v)}" r="12"/><circle class="point-focus-ring" cx="${x(i)}" cy="${y(v)}" r="8"/><circle class="point-marker" cx="${x(i)}" cy="${y(v)}" r="${total?4:3}" fill="${total?'var(--surface)':color}" stroke="${color}" stroke-width="2"/></g>`}).join("");return `<g data-series="${esc(c)}">${poly}${marks}</g>`}).join("");
 return `<article class="card chart-card" id="chart-${p.id}"><div class="chart-head"><h3>${dot(p)}${p.label}</h3><div class="chart-meta"><label class="note" for="metric-${p.id}">Metric</label><select id="metric-${p.id}" class="select chart-metric" data-metric="${p.id}">${["value",...(p.id==="podcast"?[]:["engagements",audienceKey(p)]),"posts"].map(m=>`<option value="${m}" ${s.metric===m?"selected":""}>${metricLabel(p,m)}</option>`).join("")}</select><button class="chart-reset" data-show="${p.id}">Show All</button><button class="chart-reset" data-hide="${p.id}">Deselect All</button></div></div><div class="chart-wrap"><svg class="line-chart" width="${W}" viewBox="0 0 ${W} ${H}" role="group" aria-label="${p.label} weekly ${metricLabel(p,s.metric)}">${grid}<line x1="${L}" x2="${W-R}" y1="${H-B}" y2="${H-B}" stroke="var(--axis)"/>${labels}${lines}${visible.length?"":`<text x="${W/2}" y="${H/2}" text-anchor="middle" fill="var(--muted)" font-size="14">No formats selected. Choose Show All to restore the chart.</text>`}</svg></div><div class="category-legend">${names.map(c=>`<button class="category-key ${c==="All formats"?"total ":""}${s.hidden.has(c)?"off":""}" data-toggle="${p.id}" data-category="${esc(c)}" aria-pressed="${!s.hidden.has(c)}" style="--category:${categoryColor(p,c)}"><span class="swatch"></span>${esc(c)}</button>`).join("")}</div><div class="note chart-coverage">${cutoffText(p)}${p.id==="podcast"?" · all-player downloads from Substack export":p.refresh_pending?" · awaiting updated export":p.id==="youtube"?" · reporting range unconfirmed":""}. Dashed line: all formats. ${ww.at(-1).partial?"Final week is partial.":""}${s.metric===audienceKey(p)?` ${audienceNote(p)}`:""}</div>${detail(p)}</article>`;
}

function renderChart(id,focus){
 const p=byId[id],old=$("chart-"+id),scroll=old?.querySelector(".chart-wrap")?.scrollLeft||0;
 if(old)old.outerHTML=chart(p);else $("categoryTrendCharts").insertAdjacentHTML("beforeend",chart(p));
 const el=$("chart-"+id);el.querySelector(".chart-wrap").scrollLeft=scroll;
 el.querySelector("[data-show]").onclick=()=>{state[id].hidden.clear();renderChart(id,"[data-show]")};
 el.querySelector("[data-hide]").onclick=()=>{state[id].hidden=new Set(["All formats",...cats(p)]);state[id].point=null;renderChart(id,"[data-hide]")};
 el.querySelector("[data-metric]").onchange=e=>{state[id].metric=e.target.value;renderChart(id,"[data-metric]")};
 el.querySelectorAll("[data-toggle]").forEach(b=>b.onclick=()=>{const c=b.dataset.category;state[id].hidden.has(c)?state[id].hidden.delete(c):state[id].hidden.add(c);renderChart(id,`[data-toggle][data-category="${CSS.escape(c)}"]`)});
 const close=el.querySelector("[data-close]");if(close)close.onclick=()=>{state[id].point=null;renderChart(id,".chart-point")};
 el.querySelectorAll(".chart-point").forEach(point=>{const activate=()=>{state[id].point={week:point.dataset.week,category:point.dataset.category};renderChart(id,`.chart-point[data-category="${CSS.escape(point.dataset.category)}"][data-week="${point.dataset.week}"]`)};point.onclick=activate;point.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();activate()}else if(["ArrowLeft","ArrowRight","Home","End"].includes(e.key)){e.preventDefault();const marks=[...el.querySelectorAll(".chart-point")].filter(n=>n.dataset.category===point.dataset.category),i=marks.indexOf(point),next=e.key==="Home"?0:e.key==="End"?marks.length-1:Math.max(0,Math.min(marks.length-1,i+(e.key==="ArrowRight"?1:-1)));point.tabIndex=-1;marks[next].tabIndex=0;marks[next].focus();}}});
 if(focus)el.querySelector(focus)?.focus({preventScroll:true});
}

const allWeeks=weeks.map(w=>w.start);
const latest=latestComplete(yt)?.start||allWeeks.at(-1);
function coverageText(p,w){const r=weekData(p,w);if(!covered(r))return `Unavailable · snapshot ends ${date(p.cutoff)}`;return `${status(p,w)} · ${r.posts} ${contentUnit(p)}${r.partial?` · through ${date(coveredEnd(p,r))}`:""}`}
function postTable(p,rows){return `<table><thead><tr><th scope="col">#</th><th scope="col">Published</th><th scope="col">Format</th><th scope="col">${p.id==="podcast"?"Episode":"Post"}</th><th class="n" scope="col">${unit(p)}</th><th class="n" scope="col">${p.id==="podcast"?"First 30 days":"Engagements"}</th>${audienceKey(p)?`<th class="n" scope="col">${metricLabel(p,audienceKey(p))}</th>`:""}</tr></thead><tbody>${rows.map((r,i)=>`<tr><td class="n">${i+1}</td><td style="white-space:nowrap">${date(r.date)}</td><td>${esc(r.category)}</td><td class="table-title">${titleLink(r)}</td><td class="n">${full(r.value)}</td><td class="n">${full(p.id==="podcast"?r.downloads_first_30_days:r.engagements)}</td>${audienceKey(p)?`<td class="n">${full(r[audienceKey(p)])}</td>`:""}</tr>`).join("")}</tbody></table>`}
function renderTops(w){
 $("weekSelect").value=w;document.querySelectorAll("#weekTabs button").forEach(b=>{const selected=b.dataset.week===w;b.classList.toggle("on",selected);b.setAttribute("aria-selected",String(selected));b.tabIndex=selected?0:-1});
 const selected=document.querySelector('#weekTabs [aria-selected="true"]');if(selected)$("weekTabs").scrollLeft=Math.max(0,selected.offsetLeft-$("weekTabs").offsetLeft-80);
 $("topWeekSummary").textContent=`${span(w,shift(w,6))}, 2026 · Rankings use the available export values.`;
 $("tops").innerHTML=PLATS.map(p=>{const r=weekData(p,w),rows=weekRows(p,w).filter(r=>r.value!=null).sort((a,b)=>b.value-a.value||a.title.localeCompare(b.title)).slice(0,5);return `<div class="top-platform"><div class="top-platform-head"><h3>${dot(p)}${p.label}</h3><div class="top-coverage ${!covered(r)?"unavailable":r.partial?"partial":""}">${coverageText(p,w)}</div></div>${!covered(r)?`<div class="top-empty">No source coverage for this week. Updated ${p.label} data is needed.</div>`:rows.length?`<div class="scroll">${postTable(p,rows)}</div>`:`<div class="top-empty">No ${contentUnit(p)} published in this covered week.</div>`}</div>`}).join("");
}
$("weekTabs").innerHTML=weeks.map(w=>`<button type="button" role="tab" aria-controls="tops" aria-selected="false" data-week="${w.start}"><span>${span(w.start,w.end)}</span><span class="week-tab-state">${PLATS.filter(p=>covered(weekData(p,w.start))).length} sources available</span></button>`).join("");
$("weekSelect").innerHTML=[...weeks].reverse().map(w=>`<option value="${w.start}">${span(w.start,w.end)}, 2026</option>`).join("");
document.querySelectorAll("#weekTabs button").forEach(b=>{b.onclick=()=>renderTops(b.dataset.week);b.onkeydown=e=>{if(["ArrowLeft","ArrowRight","Home","End"].includes(e.key)){e.preventDefault();const i=allWeeks.indexOf(b.dataset.week),n=e.key==="Home"?0:e.key==="End"?allWeeks.length-1:Math.max(0,Math.min(allWeeks.length-1,i+(e.key==="ArrowRight"?1:-1)));renderTops(allWeeks[n]);document.querySelector(`#weekTabs [data-week="${allWeeks[n]}"]`).focus()}}});
$("weekSelect").onchange=e=>renderTops(e.target.value);

const recent=weeks.filter(w=>w.end<=yt.cutoff).slice(-8);
$("weekly").innerHTML=`<table><thead><tr><th>Platform / metric</th>${recent.map(w=>`<th class="n">${span(w.start,w.end)}</th>`).join("")}</tr></thead><tbody>${PLATS.map(p=>`<tr><th>${dot(p)}${p.label}<div class="note">${unit(p)}</div></th>${recent.map(w=>{const r=weekData(p,w.start);return `<td class="n">${covered(r)?fmt(r.value):"—"}${covered(r)&&r.partial?'<div class="note">partial</div>':""}</td>`}).join("")}</tr>`).join("")}</tbody></table>`;

const ytRecords=records(yt),subTotal=sum(ytRecords,"subscribers_gained");
$("subscribers").innerHTML=`<div><div class="label">YouTube subscribers gained</div><div class="value">${full(subTotal)}</div><div class="detail">${cutoffText(yt)}</div></div><div>${full(sum(ytRecords.filter(r=>r.category==="Long-form"),"subscribers_gained"))} from long-form · ${full(sum(ytRecords.filter(r=>r.category==="Shorts"),"subscribers_gained"))} from Shorts<div class="detail">${audienceNote(yt)}</div></div>`;
$("followers").innerHTML=`<div><div class="label">Instagram followers gained</div><div class="value">${full(sum(records(ig),"follows"))}</div><div class="detail">${cutoffText(ig)}</div></div><div>Follows attributed to exported posts<div class="detail">${audienceNote(ig)} The source includes 26 posts credited to isthisreallylegal and 3 credited to lawyer_oyer.</div></div>`;
function renderSubscriber(){
 const all=$("subscriberRange").value==="all";
 const ww=weeks.filter(w=>[ig,yt].some(p=>covered(weekData(p,w.start)))&&(all||[ig,yt].every(p=>covered(weekData(p,w.start))&&!weekData(p,w.start).partial))).slice(all?0:-8);
 const gainCell=(p,w,c="All formats")=>{const r=weekData(p,w.start);return `<td class="n">${full(primary(p,w.start,c,audienceKey(p)))}${covered(r)&&r.partial?`<div class="note">through ${date(p.cutoff)} · partial</div>`:""}</td>`};
 $("subscriberWeekly").innerHTML=`<table><thead><tr><th>Publish week</th><th class="n">Instagram followers gained</th><th class="n">YouTube long-form</th><th class="n">YouTube Shorts</th><th class="n">YouTube subscribers gained</th></tr></thead><tbody>${ww.map(w=>`<tr><th>${span(w.start,w.end)}, 2026</th>${gainCell(ig,w)}${gainCell(yt,w,"Long-form")}${gainCell(yt,w,"Shorts")}${gainCell(yt,w)}</tr>`).join("")}</tbody></table>`;
}
$("subscriberRange").onchange=renderSubscriber;

function renderCategories(id){const p=byId[id];document.querySelectorAll("#categoryTabs button").forEach(b=>b.classList.toggle("on",b.dataset.platform===id));$("categories").innerHTML=`<table><thead><tr><th>Format</th><th class="n">${contentUnit(p)}</th><th class="n">${unit(p)}</th><th class="n">Average per item</th><th class="n">${p.id==="podcast"?"First 30 days":"Engagements"}</th></tr></thead><tbody>${cats(p).map(c=>{const rr=records(p).filter(r=>r.category===c),v=sum(rr,"value");return `<tr><td>${esc(c)}</td><td class="n">${rr.length}</td><td class="n">${full(v)}</td><td class="n">${fmt(v/rr.length)}</td><td class="n">${full(sum(rr,p.id==="podcast"?"downloads_first_30_days":"engagements"))}</td></tr>`}).join("")}</tbody></table>`}
$("categoryTabs").innerHTML=PLATS.map(p=>`<button data-platform="${p.id}">${p.label}</button>`).join("");document.querySelectorAll("#categoryTabs button").forEach(b=>b.onclick=()=>renderCategories(b.dataset.platform));

$("platformFilter").innerHTML='<option value="">All platforms</option>'+PLATS.map(p=>`<option value="${p.id}">${p.label}</option>`).join("");
function renderAll(){const q=$("search").value.toLowerCase().trim(),id=$("platformFilter").value;let count=0;$("allPosts").innerHTML=PLATS.filter(p=>!id||p.id===id).map(p=>{const rr=records(p).filter(r=>(r.title+" "+r.category).toLowerCase().includes(q)).sort((a,b)=>b.value-a.value);count+=rr.length;return `<div class="top-platform"><h3>${dot(p)}${p.label}</h3>${rr.length?postTable(p,rr):'<div class="empty">No matching content.</div>'}</div>`}).join("");$("explorerCount").textContent=`${count} matching dated items. YouTube’s 10 undated Shorts are excluded from weekly allocation and this dated-content view.`}
$("search").oninput=renderAll;$("platformFilter").onchange=renderAll;

$("definitions").innerHTML=PLATS.map(p=>`<div class="card"><h3>${dot(p)}${p.label}</h3><div class="definition"><b>Metric</b><span>${p.id==="podcast"?"All-player podcast downloads from the Substack export. Downloads are not unique audience. First 30 days shows downloads during each episode’s first 30 days, as reported in the export.":p.id==="instagram"?"Exported post views. Engagements = likes + comments + shares + saves. Followers gained uses the Follows field attributed to the supplied posts, not the current account total.":"Exported video views. Engagements = likes + comments + shares. Subscriber gains use Subscribers gained, not the separate Subscribers field or current channel audience."}</span><b>Data date</b><span>${cutoffText(p)}</span><b>Coverage</b><span>${esc(p.coverage_note)}</span></div></div>`).join("");
$("sources").innerHTML=D.notes.map(n=>`<li>${esc(typeof n==="string"?n:JSON.stringify(n))}</li>`).join("");
renderPlatforms();PLATS.forEach(p=>renderChart(p.id));renderTops(latest);renderSubscriber();renderCategories("youtube");renderAll();
