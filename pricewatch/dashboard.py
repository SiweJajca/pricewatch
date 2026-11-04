"""Generuje samodzielny plik HTML (bez serwera, bez bazy) z danymi wbudowanymi w strone."""
from __future__ import annotations

import json

I18N = {
    "pl": {
        "title": "PriceWatch", "sub": "Ceny w publicznych sklepach, sprawdzane codziennie",
        "tracked": "Produkty", "drops": "Obniżki dziś", "avg": "Średnia zmiana", "updated": "Aktualizacja",
        "search": "Szukaj produktu", "all": "Wszystkie sklepy", "onlydrops": "Tylko obniżki",
        "s_drop": "Największa obniżka", "s_asc": "Cena rosnąco", "s_desc": "Cena malejąco", "s_name": "Nazwa A–Z",
        "lowest": "Najniższa cena w historii", "promo": "Obniżka", "min": "Najniższa", "max": "Najwyższa",
        "first": "Pierwsza", "days": "Dni obserwacji", "open": "Otwórz w sklepie", "empty": "Brak produktów dla tych filtrów. Wyczyść wyszukiwanie lub wybierz inny sklep.",
        "demo": "Dane demonstracyjne: ceny wygenerowano losowo, nie pochodzą z prawdziwych sklepów.",
        "new": "nowy", "trend": "Historia ceny",
    },
    "en": {
        "title": "PriceWatch", "sub": "Prices in public online shops, checked every day",
        "tracked": "Products", "drops": "Drops today", "avg": "Average change", "updated": "Updated",
        "search": "Search products", "all": "All shops", "onlydrops": "Drops only",
        "s_drop": "Biggest drop", "s_asc": "Price: low to high", "s_desc": "Price: high to low", "s_name": "Name A–Z",
        "lowest": "Lowest price on record", "promo": "Price drop", "min": "Lowest", "max": "Highest",
        "first": "First seen", "days": "Days tracked", "open": "Open in shop", "empty": "No products match these filters. Clear the search or pick another shop.",
        "demo": "Demo data: prices are randomly generated, not taken from real shops.",
        "new": "new", "trend": "Price history",
    },
}

TEMPLATE = r"""<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>PriceWatch</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%93%89%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#e8ecf1; --card:#ffffff; --ink:#0f1b2d; --mute:#5a6678; --line:#d3d9e2;
  --promo:#ffd23f; --promo-ink:#2a2100; --down:#0a7a4c; --up:#c0392b;
  --display:"Barlow Condensed","Arial Narrow",system-ui,sans-serif;
  --body:"Barlow",system-ui,-apple-system,"Segoe UI",sans-serif;
  box-sizing:border-box; padding-top:env(safe-area-inset-top,0px); padding-bottom:env(safe-area-inset-bottom,0px);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0c131d; --card:#152131; --ink:#eaf0f7; --mute:#9aa8ba; --line:#263449;
  --promo:#ffd23f; --promo-ink:#2a2100; --down:#3ddc97; --up:#ff7b6b;}}
:root[data-theme="dark"]{
  --bg:#0c131d; --card:#152131; --ink:#eaf0f7; --mute:#9aa8ba; --line:#263449;
  --promo:#ffd23f; --promo-ink:#2a2100; --down:#3ddc97; --up:#ff7b6b;}
*{box-sizing:border-box}
html{scroll-padding-top:env(safe-area-inset-top,0px)}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.5 var(--body)}
.wrap{max-width:1180px;margin:0 auto;padding:28px 20px 56px}
h1{font:700 clamp(40px,7vw,68px)/.95 var(--display);margin:0 0 8px;letter-spacing:-.01em}
.sub{color:var(--mute);margin:0 0 22px;max-width:60ch}
.demo{background:var(--promo);color:var(--promo-ink);padding:10px 14px;border-radius:6px;font-weight:600;margin:0 0 20px}
.stats{display:flex;flex-wrap:wrap;gap:6px 34px;margin:0 0 26px;padding:0 0 18px;border-bottom:2px solid var(--ink)}
.stat b{display:block;font:700 34px/1 var(--display)}
.stat span{color:var(--mute);font-size:14px}
.tools{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 22px}
.tools input,.tools select{font:inherit;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:6px;padding:10px 12px;min-height:44px}
.tools input[type=search]{flex:1 1 220px}
.tools input[type=checkbox]{width:20px;height:20px;min-height:0;padding:0;accent-color:var(--ink)}
.tools label{white-space:nowrap}
.tools label{display:flex;align-items:center;gap:8px;min-height:44px;padding:0 4px;cursor:pointer}
:focus-visible{outline:3px solid var(--ink);outline-offset:2px}
.grid{display:grid;align-items:start;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}
.tag{background:var(--card);border:1px solid var(--line);border-radius:4px;overflow:hidden;display:flex;flex-direction:column}
.tag.drop{border:2px solid var(--ink)}
.promo{background:var(--promo);color:var(--promo-ink);font:700 18px/1 var(--display);padding:7px 12px;display:flex;justify-content:space-between}
.body{padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.shop{color:var(--mute);font-size:14px}
.name{font-weight:600;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.6em}
.priceRow{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.price{font:700 44px/1 var(--display);letter-spacing:-.01em}
.cur{font:600 20px var(--display);margin-left:3px}
.chg{font-weight:600;font-size:14px}
.chg.down{color:var(--down)} .chg.up{color:var(--up)} .chg.flat{color:var(--mute)}
.was{color:var(--mute);text-decoration:line-through;font-size:14px}
.spark{width:100%;height:auto;display:block}
.low{font-size:13px;font-weight:600;color:var(--down)}
button.more{all:unset;cursor:pointer;color:var(--mute);font-size:14px;padding:6px 0;min-height:32px}
button.more:focus-visible{outline:3px solid var(--ink)}
.detail{display:none;border-top:1px solid var(--line);padding-top:10px;font-size:14px}
.tag.open .detail{display:block}
.detail dl{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;margin:8px 0 12px}
.detail dt{color:var(--mute)} .detail dd{margin:0;font-weight:600;text-align:right}
.btn{display:inline-block;background:var(--ink);color:var(--bg);text-decoration:none;font-weight:600;padding:9px 14px;border-radius:6px}
.empty{padding:40px 0;color:var(--mute)}
@media (prefers-reduced-motion:no-preference){.detail{animation:in .18s ease-out}@keyframes in{from{opacity:0}to{opacity:1}}}
</style>
</head>
<body>
<div class="wrap">
  <h1 id="t"></h1>
  <p class="sub" id="sub"></p>
  <div id="demo"></div>
  <div class="stats" id="stats"></div>
  <div class="tools">
    <input id="q" type="search" aria-label="search">
    <select id="shop" aria-label="shop"></select>
    <select id="sort" aria-label="sort"></select>
    <label><input type="checkbox" id="only"> <span id="onlyl"></span></label>
  </div>
  <div class="grid" id="grid"></div>
</div>
<script>
const D=__DATA__, T=__I18N__, LANG="__LANG__";
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const nf=new Intl.NumberFormat(LANG,{minimumFractionDigits:2,maximumFractionDigits:2});
const money=(v,c)=>nf.format(v)+(c?'<span class="cur">'+esc(c)+'</span>':'');
const pct=v=>(v>0?"+":"")+v.toFixed(1).replace(".",LANG==="pl"?",":".")+"%";
function spark(h,w,ht){
  if(h.length<2)return"";
  const v=h.map(x=>x[1]),mn=Math.min(...v),mx=Math.max(...v),r=(mx-mn)||1,p=6;
  const pts=v.map((y,i)=>[p+i/(v.length-1)*(w-2*p),ht-p-(y-mn)/r*(ht-2*p)]);
  const line=pts.map((q,i)=>(i?"L":"M")+q[0].toFixed(1)+" "+q[1].toFixed(1)).join("");
  const area=line+"L"+pts[pts.length-1][0].toFixed(1)+" "+ht+"L"+pts[0][0].toFixed(1)+" "+ht+"Z";
  const dn=v[v.length-1]<=v[0],col=dn?"var(--down)":"var(--up)",l=pts[pts.length-1];
  return `<svg class="spark" viewBox="0 0 ${w} ${ht}" role="img" aria-label="${T.trend}"><path d="${area}" fill="${col}" opacity=".12"/><path d="${line}" fill="none" stroke="${col}" stroke-width="2" stroke-linejoin="round"/><circle cx="${l[0]}" cy="${l[1]}" r="4" fill="${col}"/></svg>`;
}
function card(i){
  const cls=i.change==null?"flat":i.change<0?"down":i.change>0?"up":"flat";
  const chg=i.change==null?T.new:(i.change<0?"▼ ":i.change>0?"▲ ":"")+pct(i.change);
  const promo=i.drop?`<div class="promo"><span>${T.promo}</span><span>${pct(i.change)}</span></div>`:"";
  return `<article class="tag ${i.drop?"drop":""}" data-id="${i.id}">${promo}<div class="body">
    <div class="shop">${esc(i.source)}</div><div class="name">${esc(i.title)}</div>
    <div class="priceRow"><span class="price">${money(i.price,i.currency)}</span>
      <span class="chg ${cls}">${chg}</span>${i.prev&&i.drop?`<span class="was">${nf.format(i.prev)}</span>`:""}</div>
    ${i.is_low?`<div class="low">${T.lowest}</div>`:""}
    ${spark(i.history,240,56)}
    <button class="more" aria-expanded="false">${T.trend} ▾</button>
    <div class="detail">${spark(i.history,520,140)}
      <dl><dt>${T.min}</dt><dd>${money(i.min,i.currency)}</dd><dt>${T.max}</dt><dd>${money(i.max,i.currency)}</dd>
      <dt>${T.first}</dt><dd>${money(i.first,i.currency)}</dd><dt>${T.days}</dt><dd>${i.history.length}</dd></dl>
      ${i.url&&i.url!=="#"?`<a class="btn" href="${esc(i.url)}" target="_blank" rel="noopener">${T.open}</a>`:""}
    </div></div></article>`;
}
function render(){
  const q=$("q").value.trim().toLowerCase(),sh=$("shop").value,so=$("sort").value,only=$("only").checked;
  let a=D.items.filter(i=>(!q||i.title.toLowerCase().includes(q))&&(!sh||i.source===sh)&&(!only||i.drop));
  const k={drop:(x,y)=>(x.change??0)-(y.change??0),asc:(x,y)=>x.price-y.price,desc:(x,y)=>y.price-x.price,name:(x,y)=>x.title.localeCompare(y.title,LANG)};
  a.sort(k[so]);
  $("grid").innerHTML=a.length?a.map(card).join(""):`<p class="empty">${T.empty}</p>`;
}
(function init(){
  document.title=T.title;$("t").textContent=T.title;$("sub").textContent=T.sub;
  $("q").placeholder=T.search;$("onlyl").textContent=T.onlydrops;
  if(D.demo)$("demo").innerHTML=`<p class="demo">${T.demo}</p>`;
  const ch=D.items.filter(i=>i.change!=null).map(i=>i.change);
  const avg=ch.length?ch.reduce((s,x)=>s+x,0)/ch.length:0;
  $("stats").innerHTML=[[D.items.length,T.tracked],[D.drops.length,T.drops],[pct(avg),T.avg],[D.updated,T.updated]]
    .map(s=>`<div class="stat"><b>${s[0]}</b><span>${s[1]}</span></div>`).join("");
  const shops=[...new Set(D.items.map(i=>i.source))].sort();
  $("shop").innerHTML=`<option value="">${T.all}</option>`+shops.map(s=>`<option>${esc(s)}</option>`).join("");
  $("sort").innerHTML=[["drop",T.s_drop],["asc",T.s_asc],["desc",T.s_desc],["name",T.s_name]].map(o=>`<option value="${o[0]}">${o[1]}</option>`).join("");
  ["q","shop","sort","only"].forEach(id=>$(id).addEventListener("input",render));
  $("grid").addEventListener("click",e=>{const b=e.target.closest("button.more");if(!b)return;
    const c=b.closest(".tag");const o=c.classList.toggle("open");b.setAttribute("aria-expanded",o);});
  render();
})();
</script>
</body>
</html>
"""


def render(view: dict, lang: str = "pl") -> str:
    lang = lang if lang in I18N else "pl"
    data = json.dumps({"updated": view["updated"], "demo": view["demo"],
                       "items": view["items"],
                       "drops": [{"id": d["id"]} for d in view["drops"]]}, ensure_ascii=False)
    data = data.replace("</", "<\\/")
    return (TEMPLATE.replace("__LANG__", lang)
            .replace("__I18N__", json.dumps(I18N[lang], ensure_ascii=False))
            .replace("__DATA__", data))
