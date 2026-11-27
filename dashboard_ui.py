"""Dashboard look & feel: templates, stylesheet and script (kept separate from dashboard.py)."""

CSS = r''':root{
  --frame:#1A1521;--frame2:#262030;--frameLine:#3A3047;--frameTx:#EAE5F1;--frameDim:#9D94AE;
  --brass:#F4B63F;--brassHi:#FFCB63;--brassDeep:#C98A12;--brassInk:#2B1D02;
  --room:#F1EEF5;--card:#fff;--line:#E1DBE9;--lineStrong:#CFC6DC;--ink:#1F1A28;--dim:#6B6479;--soft:#F7F5FA;
  --ok:#23855A;--bad:#C93C4B;--blurple:#5865F2;
  --dcBg:#313338;--dcEmbed:#2B2D31;--dcTx:#DBDEE1;--dcDim:#949BA4;
  --display:"Bricolage Grotesque","Hanken Grotesk",system-ui,sans-serif;
  --body:"Hanken Grotesk",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;font:15px/1.55 var(--body);color:var(--ink);background:var(--room)}
a{color:inherit}
h1,h2,h3{font-family:var(--display);letter-spacing:-.02em;margin:0}
button,input,select,textarea{font:inherit;color:inherit}
:focus-visible{outline:3px solid rgba(244,182,63,.55);outline-offset:2px}
.hidden{display:none!important}
svg.ic{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;flex:none}

/* ---------- frame (rail) ---------- */
.rail{position:fixed;inset:0 auto 0 0;width:248px;background:var(--frame);color:var(--frameTx);padding:22px 14px;display:flex;flex-direction:column;gap:22px;z-index:20}
.rail::before,.rail::after{content:"";position:absolute;right:-1px;width:6px;height:40px;border-radius:3px 0 0 3px;background:linear-gradient(90deg,var(--brassDeep),var(--brass));top:16%}
.rail::after{top:78%}
.rail-brand{display:flex;align-items:center;gap:12px;text-decoration:none;padding:4px 6px}
.rail-brand .mark{width:28px;height:42px;margin:0 5px;flex:none;color:var(--brass);overflow:visible}
.rail-brand b{display:block;font:700 17px/1.1 var(--display);letter-spacing:-.01em}
.rail-brand small{color:var(--frameDim);font-size:12.5px}
.rail nav{display:flex;flex-direction:column;gap:3px}
.rail nav a{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:10px;text-decoration:none;color:var(--frameDim);font-weight:600;position:relative;transition:background .15s,color .15s}
.rail nav a:hover{background:var(--frame2);color:var(--frameTx)}
.rail nav a.on{background:var(--frame2);color:#fff}
.rail nav a.on svg{color:var(--brass)}
.rail nav a.on::before{content:"";position:absolute;left:-14px;top:9px;bottom:9px;width:4px;border-radius:0 4px 4px 0;background:var(--brass)}
.rail-foot{margin-top:auto;display:flex;align-items:center;gap:10px;padding:10px;border:1px solid var(--frameLine);border-radius:12px;font-size:13px;color:var(--frameDim)}
.rail-foot img{width:32px;height:32px;border-radius:50%}
.rail-foot b{display:block;color:var(--frameTx);font-size:14px}

/* ---------- stage ---------- */
.stage{margin-left:248px;min-height:100vh}
.top{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;padding:30px 40px 6px;flex-wrap:wrap}
.top h1{font-size:34px;font-weight:700;line-height:1.1}
.top .sub{margin:6px 0 0;color:var(--dim);max-width:62ch}
.who{display:flex;align-items:center;gap:10px;font-weight:600}
.who img{width:32px;height:32px;border-radius:50%}
.who form{margin:0}
main{padding:22px 40px 90px;max-width:1280px}

.toast{display:flex;align-items:center;gap:14px;margin:14px 40px 0;padding:12px 16px;border-radius:12px;border:1px solid;animation:toastIn .35s ease-out}
.toast.ok{background:#E7F5EE;border-color:#BFE3D0;color:#14543A}
.toast.bad{background:#FDECEE;border-color:#F4C2C8;color:#8A2330}
.toast a{font-weight:700;white-space:nowrap}
.toast span{flex:1}
.toast .x{background:none;border:0;font-size:20px;line-height:1;cursor:pointer;opacity:.6}
@keyframes toastIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}

/* ---------- controls ---------- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:10px 16px;border-radius:10px;border:1px solid transparent;font-weight:700;font-size:14px;cursor:pointer;text-decoration:none;transition:background .15s,border-color .15s,transform .05s;background:var(--soft)}
.btn:active{transform:translateY(1px)}
.btn.brass{background:var(--brass);color:var(--brassInk)}.btn.brass:hover{background:var(--brassHi)}
.btn.plum{background:#2C2439;color:#fff}.btn.plum:hover{background:#3A2F4C}
.btn.ghost{background:#fff;border-color:var(--lineStrong)}.btn.ghost:hover{border-color:var(--ink)}
.btn.danger{background:#fff;border-color:#EDBFC5;color:var(--bad)}.btn.danger:hover{background:#FDECEE}
.btn.quiet{background:transparent;color:var(--dim)}.btn.quiet:hover{color:var(--ink);background:rgba(31,26,40,.06)}
.btn.blurple{background:var(--blurple);color:#fff}.btn.blurple:hover{background:#6B77F6}
.btn.sm{padding:6px 11px;font-size:13px;border-radius:8px}
.btn.lg{padding:14px 26px;font-size:16px;border-radius:12px}
.btn[disabled]{opacity:.5;cursor:not-allowed}
.who .btn.quiet{padding:6px 10px}

.field{display:grid;gap:6px;margin-bottom:18px;min-width:0}
.field>label,.lbl{font-weight:700;font-size:13.5px}
.hint{color:var(--dim);font-size:13px;margin:0}
input[type=text],input[type=url],input[type=search],select,textarea{width:100%;background:#fff;border:1px solid var(--lineStrong);border-radius:10px;padding:10px 12px;transition:border-color .15s,box-shadow .15s}
textarea{resize:vertical;min-height:96px;line-height:1.5}
input:focus,select:focus,textarea:focus{outline:none;border-color:var(--brassDeep);box-shadow:0 0 0 3px rgba(244,182,63,.3)}
input[type=color]{width:46px;height:42px;padding:3px;border:1px solid var(--lineStrong);border-radius:10px;background:#fff;cursor:pointer}
.row{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-end}
.row>.field{flex:1 1 180px}
.inline{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.split{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.counter{font-size:12px;color:var(--dim);justify-self:end}
.check{display:flex;gap:10px;align-items:flex-start;font-weight:600;cursor:pointer}
.check input{margin-top:4px;accent-color:var(--brassDeep);width:17px;height:17px}
.check small{display:block;font-weight:400;color:var(--dim)}
.colorfield{display:flex;gap:10px;align-items:center}
.colorfield code{font-size:13px;color:var(--dim)}
.imgfield{display:grid;gap:8px}
.imgfield .line{display:flex;gap:8px}
.imgfield .thumb{width:100%;max-height:120px;object-fit:cover;border-radius:10px;border:1px solid var(--line);background:var(--soft)}
.ai-btn{justify-self:start}
.ai-btn svg{width:17px;height:17px}

/* ---------- layout blocks ---------- */
.editor{display:grid;grid-template-columns:minmax(0,1fr) 410px;gap:34px;align-items:start}
.pv-col{position:sticky;top:22px;display:grid;gap:14px}
.sheet{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:26px}
.sheet+.sheet{margin-top:20px}
.sheet h2{font-size:20px;margin-bottom:4px}
.sheet>.hint:first-of-type,.sheet h2+.hint{margin-bottom:18px}
.actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:6px}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--lineStrong);margin-bottom:26px;overflow-x:auto}
.tab{background:none;border:1px solid transparent;border-bottom:0;padding:11px 18px;border-radius:12px 12px 0 0;font-weight:700;color:var(--dim);cursor:pointer;margin-bottom:-1px;white-space:nowrap;position:relative}
.tab:hover{color:var(--ink)}
.tab.on{background:var(--room);color:var(--ink);border-color:var(--lineStrong);border-bottom:1px solid var(--room)}
.tab.on::before{content:"";position:absolute;left:14px;right:14px;top:-1px;height:3px;border-radius:0 0 3px 3px;background:var(--brass)}
.tabpane{display:none}.tabpane.on{display:block}
.empty{padding:38px 20px;text-align:center;color:var(--dim);border:2px dashed var(--lineStrong);border-radius:16px}
.empty b{display:block;color:var(--ink);font:700 18px var(--display);margin-bottom:4px}
.chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:99px;font-size:12.5px;font-weight:700;background:var(--soft);border:1px solid var(--line)}
.chip.live{background:#E7F5EE;border-color:#BFE3D0;color:#14543A}
.chip.paused{background:#FFF4DD;border-color:#F2DCA8;color:#7A5200}
.vars{display:flex;gap:6px;flex-wrap:wrap}
.vars code,code.v{background:var(--soft);border:1px solid var(--line);padding:1px 7px;border-radius:6px;font-size:12.5px}
.opt{display:flex;gap:14px;padding:16px 18px;border:1px solid var(--lineStrong);border-radius:14px;cursor:pointer;margin-bottom:10px;background:#fff;transition:border-color .15s,background .15s}
.opt:hover{border-color:var(--ink)}
.opt input{margin-top:5px;accent-color:var(--brassDeep);width:18px;height:18px}
.opt:has(input:checked){border-color:var(--brassDeep);background:#FFFAEE}
.opt b{display:block}.opt span{color:var(--dim);font-size:14px}

/* ---------- home doors ---------- */
.hello{font:700 44px/1.05 var(--display);letter-spacing:-.03em;margin:4px 0 6px}
.hello+p{color:var(--dim);margin:0 0 26px}
.doors{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-bottom:34px}
.dtile{position:relative;display:flex;flex-direction:column;justify-content:flex-end;min-height:268px;padding:22px 24px;background:#fff;border:1px solid var(--line);border-radius:14px;text-decoration:none;transition:border-color .2s,transform .2s,box-shadow .2s;--dc:var(--brass)}
.dtile:hover,.dtile:focus-visible{border-color:var(--dc);transform:translateY(-3px);box-shadow:0 14px 30px -18px var(--dc)}
.dtile .dg{position:absolute;top:24px;left:50%;margin-left:-35px;width:70px;height:105px;perspective:420px;color:var(--dc)}
.dtile .hole{position:absolute;inset:0;background:var(--dc);opacity:.16;border-radius:2px;transition:opacity .3s}
.dtile .dg .lf{position:absolute;inset:0;width:100%;height:100%;transform-origin:left center;transition:transform .5s cubic-bezier(.5,.1,.2,1);overflow:visible}
.dtile:hover .hole,.dtile:focus-visible .hole{opacity:.55}
.dtile:hover .dg .lf,.dtile:focus-visible .dg .lf{transform:rotateY(-52deg)}
.dtile b{font:700 20px var(--display)}
.dtile span{color:var(--dim);font-size:14px}
.stats{display:flex;gap:34px;flex-wrap:wrap;margin-bottom:30px}
.stats div{min-width:110px}
.stats b{display:block;font:700 26px var(--display)}
.stats span{color:var(--dim);font-size:13.5px}
.todo{list-style:none;margin:0;padding:0}
.todo li{display:flex;gap:14px;align-items:flex-start;padding:13px 0;border-top:1px solid var(--line)}
.todo li:first-child{border-top:0}
.todo .mk{width:22px;height:22px;border-radius:50%;display:grid;place-items:center;flex:none;margin-top:1px;font-size:13px;font-weight:800}
.todo .yes .mk{background:var(--ok);color:#fff}
.todo .no .mk{background:#fff;border:2px solid var(--lineStrong);color:transparent}
.todo b{display:block}.todo small{color:var(--dim)}

/* ---------- preview door ---------- */
.door{position:relative;background:var(--frame);border-radius:14px;padding:14px 14px 16px;box-shadow:0 22px 40px -26px rgba(26,21,33,.8)}
.door-head{display:flex;align-items:center;gap:8px;color:var(--frameDim);font-size:12.5px;font-weight:600;padding:3px 8px 11px}
.door-head i{width:8px;height:8px;border-radius:50%;background:var(--brass)}
.door .knob{position:absolute;right:-7px;top:46%;width:15px;height:15px;border-radius:50%;background:radial-gradient(circle at 30% 30%,#ffe19a,var(--brass) 55%,#b9791a);box-shadow:0 1px 3px rgba(0,0,0,.5)}
.dc{background:var(--dcBg);border-radius:12px;padding:16px 14px;color:var(--dcTx);font:15px/1.4 "gg sans","Noto Sans","Helvetica Neue",sans-serif;display:grid;gap:18px;overflow:hidden}
.dc-msg{display:grid;grid-template-columns:40px 1fr;gap:12px}
.dc-av{width:40px;height:40px;border-radius:50%;object-fit:cover;background:#5865F2}
.dc-name{font-weight:600;color:#fff;margin-bottom:2px}
.dc-tag{background:#5865F2;color:#fff;border-radius:4px;font-size:10px;padding:1px 5px;margin-left:4px;vertical-align:2px;font-weight:700}
.dc-name time{color:var(--dcDim);font-weight:400;font-size:12px;margin-left:6px}
.dc-content{white-space:pre-wrap;word-break:break-word;min-height:0}
.dc-content:empty{display:none}
.dc-content sub,.dc-sub{display:block;font-size:12px;color:var(--dcDim);line-height:1.3}
.dc-embed{margin-top:6px;max-width:430px}
.dc-embed:empty{display:none}
.e-box{display:grid;grid-template-columns:1fr auto;gap:4px 14px;border-left:4px solid var(--c,#FFFF00);background:var(--dcEmbed);border-radius:4px;padding:8px 14px 14px 12px}
.e-title{font-weight:700;color:#fff;grid-column:1;margin-top:6px;word-break:break-word}
.e-desc{grid-column:1;font-size:14px;white-space:pre-wrap;word-break:break-word;margin-top:6px}
.e-thumb{grid-column:2;grid-row:1/4;width:64px;height:64px;object-fit:cover;border-radius:6px;margin-top:6px}
.e-img{grid-column:1/-1;width:100%;max-height:260px;object-fit:cover;border-radius:6px;margin-top:10px}
.e-foot{grid-column:1/-1;font-size:12px;color:var(--dcDim);margin-top:10px}
.dc-buttons{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.dcb{padding:2px 14px;min-height:32px;display:inline-flex;align-items:center;border-radius:4px;font-size:14px;font-weight:500;color:#fff;background:#4E5058}
.dcb.primary{background:#5865F2}.dcb.success{background:#248046}.dcb.danger{background:#DA373C}.dcb.secondary{background:#4E5058}
.dc-files{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.dc-file{background:var(--dcEmbed);border:1px solid #1E1F22;border-radius:6px;padding:8px 12px;font-size:13px}
.mention{background:rgba(88,101,242,.3);color:#C9CDFB;border-radius:3px;padding:0 2px;font-weight:500}
.dc code{background:#1E1F22;border-radius:4px;padding:1px 5px;font-size:13px}
.dc blockquote{margin:2px 0;padding-left:10px;border-left:4px solid #4E5058}
.pvnote{color:var(--dim);font-size:13px;margin:0 4px}

/* ---------- tickets (products) ---------- */
.stub{position:relative;background:#fff;border:1px solid var(--line);border-radius:16px;margin-bottom:22px;overflow:hidden;display:grid;grid-template-columns:minmax(0,1fr) 1px 380px}
.stub .perf{background:repeating-linear-gradient(to bottom,var(--lineStrong) 0 6px,transparent 6px 12px);position:relative}
.stub .perf::before,.stub .perf::after{content:"";position:absolute;left:-12px;width:24px;height:24px;border-radius:50%;background:var(--room);border:1px solid var(--line)}
.stub .perf::before{top:-13px}.stub .perf::after{bottom:-13px}
.stub .body{padding:24px 26px}
.stub .side{padding:22px 20px;background:var(--soft)}
.stub.new{border-style:dashed;border-color:var(--lineStrong)}
.stub h3{font-size:18px;margin-bottom:14px;display:flex;justify-content:space-between;gap:10px;align-items:center}
.reorder{display:inline-flex;gap:4px}
.reorder button{width:30px;height:30px;border-radius:8px;border:1px solid var(--lineStrong);background:#fff;cursor:pointer;display:grid;place-items:center}
.reorder button:hover{border-color:var(--ink)}
.reorder form{margin:0}

/* ---------- lists ---------- */
.list{display:grid;gap:12px}
.item{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:center;padding:16px 18px;background:#fff;border:1px solid var(--line);border-radius:14px}
.item h3{font-size:16px;margin-bottom:2px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.item p{margin:2px 0 0;color:var(--dim);font-size:14px;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.item .acts{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.item form{margin:0}
.tbl{width:100%;border-collapse:collapse}
.tbl th{text-align:left;color:var(--dim);font-size:13px;font-weight:700;padding:8px 8px}
.tbl td{padding:12px 8px;border-top:1px solid var(--line);vertical-align:middle}
.tbl td form{display:inline-flex;gap:6px;margin:0}
.tbl select{width:auto;min-width:150px}
.scroll{overflow-x:auto}
code{background:var(--soft);padding:2px 6px;border-radius:6px;font-size:13px;word-break:break-all}

/* members */
.mrow{display:grid;grid-template-columns:44px minmax(0,1fr) auto;gap:14px;align-items:start;padding:16px 4px;border-top:1px solid var(--line)}
.mrow:first-child{border-top:0}
.mrow img{width:44px;height:44px;border-radius:50%}
.mrow h3{font:700 16px var(--display);display:flex;gap:8px;align-items:center}
.mrow small{color:var(--dim);font-weight:500;font-family:var(--body)}
.rchips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.rchip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--lineStrong);border-radius:99px;padding:2px 4px 2px 10px;font-size:13px;font-weight:600;background:#fff}
.rchip i{width:10px;height:10px;border-radius:50%;background:var(--rc)}
.rchip form{display:inline;margin:0}
.rchip button{border:0;background:var(--soft);width:20px;height:20px;border-radius:50%;cursor:pointer;line-height:1;color:var(--dim)}
.rchip button:hover{background:var(--bad);color:#fff}
.rchip.locked{padding-right:10px;color:var(--dim)}
.addrole{display:flex;gap:6px}
.addrole select{width:170px}

/* profile card */
.pcard{border-radius:16px;overflow:hidden;background:#232428;color:#DBDEE1;max-width:340px;box-shadow:0 18px 40px -26px rgba(0,0,0,.8)}
.pcard .banner{height:120px;background:#5865F2 center/cover no-repeat}
.pcard .av{width:88px;height:88px;border-radius:50%;border:6px solid #232428;margin:-46px 0 0 16px;background:#5865F2;object-fit:cover;display:block}
.pcard .pb{padding:8px 18px 18px}
.pcard h3{font:700 20px var(--display);color:#fff}
.pcard .about{background:#111214;border-radius:10px;padding:12px;margin-top:12px;font-size:14px;white-space:pre-wrap}
.pcard .about b{display:block;font-size:12px;margin-bottom:4px;color:#fff}

/* ---------- dialog (AI) ---------- */
dialog{border:0;border-radius:20px;padding:0;width:min(640px,94vw);box-shadow:0 30px 80px -20px rgba(0,0,0,.55);color:var(--ink)}
dialog::backdrop{background:rgba(26,21,33,.62);backdrop-filter:blur(3px)}
.dlg-h{display:flex;justify-content:space-between;align-items:center;padding:20px 26px;background:var(--frame);color:#fff}
.dlg-h h2{font-size:20px}
.dlg-h button{background:none;border:0;color:#fff;font-size:24px;cursor:pointer}
.dlg-b{padding:24px 26px 26px}
.pills{display:flex;gap:6px;flex-wrap:wrap}
.pill{border:1px solid var(--lineStrong);background:#fff;border-radius:99px;padding:6px 14px;font-weight:600;font-size:13.5px;cursor:pointer}
.pill.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.spin{display:inline-block;width:14px;height:14px;border:2px solid currentColor;border-right-color:transparent;border-radius:50%;animation:sp .7s linear infinite;vertical-align:-2px}
@keyframes sp{to{transform:rotate(360deg)}}
.err{color:var(--bad);font-weight:600;margin:8px 0 0}

/* ---------- login ---------- */
body.login{background:radial-gradient(1200px 700px at 50% 30%,#2A2036 0,#17121D 60%);min-height:100vh;display:grid;place-items:center;color:#fff;overflow:hidden}
.scene{display:grid;justify-items:center;gap:26px;padding:24px;perspective:1400px}
.doorway{position:relative;width:min(80vw,340px);aspect-ratio:274/410;background:#000;box-shadow:0 40px 80px -30px #000,0 0 70px -6px rgba(244,182,63,.3);color:#F4EFE6}
.room{position:absolute;inset:0;display:grid;align-content:center;justify-items:center;gap:14px;text-align:center;padding:34px 22px 22px;background:radial-gradient(circle at 50% 38%,rgba(244,182,63,.42),rgba(244,182,63,.08) 55%,transparent 75%),#171220}
.room h1{font-size:28px;font-weight:800}
.room p{margin:0;color:#C5BBD6;max-width:28ch}
.leaf{position:absolute;inset:0;transform-origin:left center;backface-visibility:hidden;animation:openDoor 1.7s .5s cubic-bezier(.6,.05,.25,1) forwards}
.leaf .tdsdoor{display:block;width:100%;height:100%}
.doorway::after{content:"";position:absolute;inset:0;border:5px solid #F4EFE6;pointer-events:none}
@keyframes openDoor{to{transform:rotateY(-108deg)}}
.room>*{opacity:0;animation:fadeUp .6s 1.5s ease-out forwards}
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.closed .leaf{animation:none}.closed .room>*{animation:none;opacity:1}
.note{max-width:420px;text-align:center;color:#B9AFCB;font-size:14px}
.note code{background:#2A2036;color:#fff}
.note b{color:#fff}
.deny-id{display:inline-block;margin-top:6px;background:#2A2036;border:1px solid #3A3047;padding:6px 12px;border-radius:8px;font-size:14px;user-select:all}

@media (max-width:1080px){
  .editor{grid-template-columns:1fr}.pv-col{position:static;order:-1}
  .stub{grid-template-columns:1fr}.stub .perf{height:1px;background:repeating-linear-gradient(to right,var(--lineStrong) 0 6px,transparent 6px 12px)}
  .stub .perf::before{left:-13px;top:-12px}.stub .perf::after{left:auto;right:-13px;top:-12px;bottom:auto}
  .doors{grid-template-columns:repeat(2,1fr)}
}
@media (max-width:860px){
  .rail{position:static;width:auto;flex-direction:row;align-items:center;padding:10px 12px;gap:10px;overflow-x:auto}
  .rail::before,.rail::after,.rail-foot,.rail-brand small,.rail-brand b,.rail nav a.on::before{display:none}
  .rail nav{flex-direction:row}.rail nav a{padding:8px 10px;white-space:nowrap}
  .stage{margin-left:0}.top,main{padding-left:18px;padding-right:18px}.toast{margin-left:18px;margin-right:18px}
  .top h1{font-size:27px}.hello{font-size:34px}.split{grid-template-columns:1fr}.doors{grid-template-columns:1fr}
  .mrow{grid-template-columns:44px 1fr}.mrow>.addrole{grid-column:1/-1}.item{grid-template-columns:1fr}.item .acts{justify-content:flex-start}
}
@media (prefers-reduced-motion:reduce){
  .leaf{animation:none;display:none}.room>*{animation:none;opacity:1}.toast{animation:none}
  *{transition:none!important}
}
'''

JS = r'''(function () {
  'use strict';
  var BOOT = {};
  try { BOOT = JSON.parse(document.getElementById('boot').textContent) || {}; } catch (e) {}
  BOOT.assets = BOOT.assets || {};
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
  function fill(t, vars) { return String(t || '').replace(/\{(\w+)\}/g, function (m, k) { return k in vars ? vars[k] : m; }); }
  function imgUrl(v) { v = (v || '').trim(); return v.indexOf('asset:') === 0 ? (BOOT.assets[v] || '') : (/^https?:\/\//.test(v) ? v : ''); }

  /* ---------- Discord-style markdown (subset) ---------- */
  function inline(s) {
    s = s.replace(/`([^`\n]+)`/g, '<code>$1</code>');
    s = s.replace(/\*\*([^\n]+?)\*\*/g, '<b>$1</b>');
    s = s.replace(/__([^\n]+?)__/g, '<u>$1</u>');
    s = s.replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, '$1<i>$2</i>');
    s = s.replace(/~~([^\n]+?)~~/g, '<s>$1</s>');
    s = s.replace(/&lt;@&amp;(\d+)&gt;/g, function (m, id) { return '<span class="mention">@' + esc((BOOT.roles || {})[id] || 'role') + '</span>'; });
    s = s.replace(/&lt;@!?(\d+)&gt;/g, '<span class="mention">@user</span>');
    s = s.replace(/&lt;#(\d+)&gt;/g, '<span class="mention">#channel</span>');
    s = s.replace(/&lt;a?:(\w+):\d+&gt;/g, ':$1:');
    s = s.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" style="color:#00A8FC" target="_blank" rel="noopener">$1</a>');
    return s;
  }
  function md(src) {
    var lines = esc(src || '').split('\n'), out = '', prevBlock = true;
    lines.forEach(function (line, i) {
      var block = true, html;
      if (/^-# /.test(line)) html = '<span class="dc-sub">' + inline(line.slice(3)) + '</span>';
      else if (/^&gt; /.test(line)) html = '<blockquote>' + inline(line.slice(5)) + '</blockquote>';
      else if (/^[-*] /.test(line)) { html = '<div>• ' + inline(line.slice(2)) + '</div>'; }
      else if (/^#{1,3} /.test(line)) html = '<div style="font-weight:700;font-size:1.2em;margin:4px 0">' + inline(line.replace(/^#{1,3} /, '')) + '</div>';
      else { html = inline(line); block = false; }
      if (i > 0 && !block && !prevBlock) out += '\n';
      out += html; prevBlock = block;
    });
    return out;
  }

  /* ---------- message preview ---------- */
  function buildMsg(m) {
    var w = document.createElement('div'); w.className = 'dc-msg';
    var h = '<img class="dc-av" src="' + esc(BOOT.bot_avatar || '') + '" alt=""><div><div class="dc-name">' + esc(BOOT.bot_name || 'Bot') +
      ' <span class="dc-tag">APP</span><time>Today</time></div>';
    if (m.content) h += '<div class="dc-content">' + md(m.content) + '</div>';
    var e = m.embed;
    if (e && (e.title || e.description || e.image || e.thumbnail)) {
      h += '<div class="dc-embed"><div class="e-box" style="--c:' + esc(e.color || '#FFFF00') + '">';
      if (e.title) h += '<div class="e-title">' + inline(esc(e.title)) + '</div>';
      if (e.description) h += '<div class="e-desc">' + md(e.description) + '</div>';
      if (imgUrl(e.thumbnail)) h += '<img class="e-thumb" src="' + esc(imgUrl(e.thumbnail)) + '" alt="">';
      if (imgUrl(e.image)) h += '<img class="e-img" src="' + esc(imgUrl(e.image)) + '" alt="">';
      if (e.footer) h += '<div class="e-foot">' + esc(e.footer) + '</div>';
      h += '</div></div>';
    }
    if (m.files && m.files.length) h += '<div class="dc-files">' + m.files.map(function (f) { return '<div class="dc-file">📎 ' + esc(f) + '</div>'; }).join('') + '</div>';
    if (m.buttons && m.buttons.length) h += '<div class="dc-buttons">' + m.buttons.map(function (b) { return '<span class="dcb ' + esc(b.style || 'primary') + '">' + esc(b.label || 'Button') + '</span>'; }).join('') + '</div>';
    w.innerHTML = h + '</div>';
    return w;
  }
  function val(form, name) { var el = form.elements[name]; return el ? el.value : ''; }
  var VARS = { product: 'Chasing Sunset Tee', price: '500', note: '\n🔥 Your sample note shows here.', user: '@Doorling' };
  var ADAPT = {
    panel: function (f) {
      return [{ embed: { title: val(f, 'title'), description: val(f, 'description'), color: val(f, 'color'), image: val(f, 'image'), thumbnail: val(f, 'thumbnail'), footer: val(f, 'footer') },
        buttons: [{ label: val(f, 'button_label'), style: val(f, 'button_style') }] }];
    },
    ticket: function (f) {
      var v = { user: '@Doorling' };
      return [{ content: '🔔 @Admin @TDS - Members — **New Merch Order Ticket opened by @Doorling!**',
        embed: { title: val(f, 'title'), description: fill(val(f, 'description'), v), color: val(f, 'color'), image: val(f, 'image'), thumbnail: val(f, 'thumbnail') },
        buttons: BOOT.products || [] }];
    },
    product: function (f) {
      var R = BOOT.reply || {}, note = val(f, 'note'), v = { product: val(f, 'name') || 'Item', price: val(f, 'price') || '0', note: note ? '\n' + note : '', user: '@Doorling' };
      return [{ content: fill(R.message, v),
        embed: { title: fill(R.embed_title, v), description: fill(R.embed_description, v), color: R.color, image: val(f, 'image'), thumbnail: val(f, 'thumbnail'), footer: 'Order item: ' + v.product },
        buttons: [{ label: R.yes_label, style: 'success' }, { label: R.no_label, style: 'danger' }] }];
    },
    reply: function (f) {
      var S = BOOT.sample || {}, v = { product: S.name || VARS.product, price: S.price || VARS.price, note: S.note ? '\n' + S.note : VARS.note, user: VARS.user };
      return [{ content: fill(val(f, 'message'), v),
        embed: { title: fill(val(f, 'embed_title'), v), description: fill(val(f, 'embed_description'), v), color: val(f, 'color'), image: S.image, thumbnail: S.thumbnail, footer: 'Order item: ' + v.product },
        buttons: [{ label: val(f, 'yes_label'), style: 'success' }, { label: val(f, 'no_label'), style: 'danger' }] },
        { content: val(f, 'form_text') }];
    },
    close: function (f) { return [{ content: val(f, 'message'), buttons: [{ label: val(f, 'label'), style: 'danger' }] }]; },
    sticky: function (f) {
      if (val(f, 'mode') === 'embed') return [{ embed: { title: val(f, 'title'), description: val(f, 'content'), color: val(f, 'color'), image: val(f, 'image'), footer: '📌 Sticky' } }];
      return [{ content: val(f, 'content') + '\n-# 📌 Sticky' }];
    },
    send: function (f) {
      var sel = f.elements.ping_role, role = sel && sel.value ? '<@&' + sel.value + '> ' : '';
      var files = f.elements.files ? Array.prototype.map.call(f.elements.files.files, function (x) { return x.name; }) : [];
      if (val(f, 'mode') === 'embed') return [{ content: role.trim(), embed: { title: val(f, 'title'), description: val(f, 'content'), color: val(f, 'color'), image: val(f, 'image') }, files: files }];
      return [{ content: role + val(f, 'content'), files: files }];
    }
  };
  function initPreview(el) {
    var form = $(el.getAttribute('data-form')); if (!form) return;
    var run = ADAPT[el.getAttribute('data-kind')]; if (!run) return;
    var dc = $('.dc', el);
    function render() { dc.innerHTML = ''; run(form).forEach(function (m) { dc.appendChild(buildMsg(m)); }); }
    form.addEventListener('input', render); form.addEventListener('change', render); render();
    form._render = render;
  }

  /* ---------- tabs ---------- */
  function initTabs() {
    var tabs = $$('.tab[data-tab]'); if (!tabs.length) return;
    function show(name) {
      tabs.forEach(function (t) { t.classList.toggle('on', t.dataset.tab === name); });
      $$('.tabpane').forEach(function (p) { p.classList.toggle('on', p.id === 'tab-' + name); });
      var u = new URL(location.href); u.searchParams.set('tab', name); history.replaceState(null, '', u);
    }
    tabs.forEach(function (t) { t.addEventListener('click', function () { show(t.dataset.tab); }); });
    var want = new URL(location.href).searchParams.get('tab');
    show(tabs.some(function (t) { return t.dataset.tab === want; }) ? want : tabs[0].dataset.tab);
  }

  /* ---------- small helpers ---------- */
  function initMisc() {
    $$('.toast .x').forEach(function (b) { b.addEventListener('click', function () { b.parentNode.remove(); }); });
    $$('form[data-confirm]').forEach(function (f) { f.addEventListener('submit', function (e) { if (!confirm(f.dataset.confirm)) e.preventDefault(); }); });
    $$('.colorfield input[type=color]').forEach(function (c) {
      var code = c.parentNode.querySelector('code');
      c.addEventListener('input', function () { if (code) code.textContent = c.value.toUpperCase(); });
    });
    $$('[data-count]').forEach(function (t) {
      var max = +t.dataset.count, out = t.parentNode.querySelector('.counter');
      function upd() { if (out) { out.textContent = t.value.length + ' / ' + max; out.style.color = t.value.length > max ? 'var(--bad)' : ''; } }
      t.addEventListener('input', upd); upd();
    });
    $$('form').forEach(function (f) {
      var whens = $$('[data-when]', f); if (!whens.length) return;
      function upd() {
        whens.forEach(function (el) {
          var p = el.dataset.when.split(':'), cur = f.elements[p[0]], v = cur ? (cur.length && cur[0] && cur[0].type === 'radio' ? (f.querySelector('[name=' + p[0] + ']:checked') || {}).value : cur.value) : '';
          el.classList.toggle('hidden', p[1].split(',').indexOf(v) < 0);
        });
      }
      f.addEventListener('change', upd); f.addEventListener('input', upd); upd();
    });
    $$('input[type=file][data-img-preview]').forEach(function (inp) {
      inp.addEventListener('change', function () {
        var f = inp.files[0], t = $(inp.dataset.imgPreview); if (!f || !t) return;
        var url = URL.createObjectURL(f);
        if (t.tagName === 'IMG') t.src = url; else t.style.backgroundImage = 'url(' + url + ')';
      });
    });
    $$('[data-mirror]').forEach(function (src) {
      var t = $(src.dataset.mirror); if (!t) return;
      function upd() { t.textContent = src.value || ' '; } src.addEventListener('input', upd); upd();
    });
    var drop = $('.drop');
    if (drop) {
      var inp = $('input[type=file]', drop);
      ['dragover', 'dragenter'].forEach(function (ev) { drop.addEventListener(ev, function (e) { e.preventDefault(); drop.style.borderColor = 'var(--brassDeep)'; }); });
      ['dragleave', 'drop'].forEach(function (ev) { drop.addEventListener(ev, function () { drop.style.borderColor = ''; }); });
      drop.addEventListener('drop', function (e) { e.preventDefault(); inp.files = e.dataTransfer.files; inp.dispatchEvent(new Event('change', { bubbles: true })); });
      inp.addEventListener('change', function () {
        var list = $('.drop-list', drop);
        list.textContent = Array.prototype.map.call(inp.files, function (f) { return f.name + ' (' + (f.size / 1048576).toFixed(1) + ' MB)'; }).join('  •  ') || 'No files chosen';
      });
    }
  }

  /* ---------- image upload ---------- */
  function initImages() {
    $$('.imgfield').forEach(function (box) {
      var txt = $('input[type=text]', box), thumb = $('.thumb', box), btn = $('.upl', box), file = $('input[type=file]', box);
      function sync() { var u = imgUrl(txt.value); if (thumb) { thumb.classList.toggle('hidden', !u); if (u) thumb.src = u; } }
      txt.addEventListener('input', sync); sync();
      if (!btn) return;
      btn.addEventListener('click', function () { file.click(); });
      file.addEventListener('change', function () {
        if (!file.files[0]) return;
        var fd = new FormData(); fd.append('file', file.files[0]);
        btn.disabled = true; var old = btn.textContent; btn.innerHTML = '<span class="spin"></span> Uploading';
        fetch('/admin/upload-image', { method: 'POST', headers: { 'X-CSRF': BOOT.csrf }, body: fd, credentials: 'same-origin' })
          .then(function (r) { return r.json(); })
          .then(function (j) {
            if (!j.ok) throw new Error(j.error || 'Upload failed');
            BOOT.assets[j.ref] = j.url; txt.value = j.ref; sync();
            txt.dispatchEvent(new Event('input', { bubbles: true }));
          })
          .catch(function (e) { alert(e.message); })
          .finally(function () { btn.disabled = false; btn.textContent = old; file.value = ''; });
      });
    });
  }

  /* ---------- AI helper ---------- */
  function initAI() {
    var dlg = $('#ai-modal'); if (!dlg) return;
    var target = null, tone = 'friendly and upbeat';
    var out = $('#ai-out'), err = $('#ai-err'), go = $('#ai-go'), use = $('#ai-use'), prompt = $('#ai-prompt'), kind = $('#ai-kind');
    var limit = 1800;
    $$('.pill', dlg).forEach(function (p) { p.addEventListener('click', function () { $$('.pill', dlg).forEach(function (x) { x.classList.remove('on'); }); p.classList.add('on'); tone = p.dataset.tone; }); });
    $$('[data-ai]').forEach(function (b) {
      b.addEventListener('click', function () {
        target = $(b.dataset.ai); if (!target) return;
        kind.value = b.dataset.kind || 'post'; limit = +b.dataset.limit || 1800;
        $('#ai-rewrite-wrap').classList.toggle('hidden', !target.value.trim());
        out.value = ''; err.textContent = ''; use.disabled = true;
        if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
        prompt.focus();
      });
    });
    $('#ai-close').addEventListener('click', function () { dlg.close(); });
    go.addEventListener('click', function () {
      err.textContent = ''; go.disabled = true; var old = go.innerHTML; go.innerHTML = '<span class="spin"></span> Writing…';
      var rewrite = $('#ai-rewrite').checked && target.value.trim();
      fetch('/admin/ai', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF': BOOT.csrf },
        body: JSON.stringify({ kind: kind.value, tone: tone, language: $('#ai-lang').value, prompt: prompt.value, current: rewrite ? target.value : '', limit: limit }) })
        .then(function (r) { return r.json(); })
        .then(function (j) { if (!j.ok) throw new Error(j.error || 'Something went wrong'); out.value = j.text; use.disabled = false; })
        .catch(function (e) { err.textContent = e.message; })
        .finally(function () { go.disabled = false; go.innerHTML = old; });
    });
    use.addEventListener('click', function () {
      target.value = out.value; target.dispatchEvent(new Event('input', { bubbles: true })); dlg.close(); target.focus();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTabs(); initMisc(); initImages(); initAI();
    $$('[data-pv]').forEach(initPreview);
  });
})();
'''

TEMPLATES = {
    'base.html': r'''{% from "macros.html" import icon, csrf_field, tds_door with context %}<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><meta name="theme-color" content="#1A1521">
<title>{% block title %}{{ page_title }}{% endblock %} · The Door Stoppers</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 60'%3E%3Crect width='40' height='60' rx='6' fill='%231A1521'/%3E%3Cg fill='none' stroke='%23F4B63F' stroke-width='2.6'%3E%3Crect x='7' y='8' width='26' height='44'/%3E%3Crect x='12' y='13' width='14' height='13'/%3E%3Crect x='12' y='34' width='14' height='13'/%3E%3C/g%3E%3C/svg%3E">
<link rel="stylesheet" href="/admin/assets/app.css?v={{ v }}"></head>
<body>
<aside class="rail">
  <a class="rail-brand" href="/admin">{{ tds_door("mark") }}<span><b>The Door Stoppers</b><small>Control room</small></span></a>
  <nav aria-label="Main">{% for key, href, label, ic in nav %}<a href="{{ href }}" class="{{ 'on' if key == active }}"{% if key == active %} aria-current="page"{% endif %}>{{ icon(ic) }}<span>{{ label }}</span></a>{% endfor %}</nav>
  <div class="rail-foot">{% if bot_avatar %}<img src="{{ bot_avatar }}" alt="">{% endif %}<div><b>{{ bot_name }}</b>Online</div></div>
</aside>
<div class="stage">
  <header class="top"><div><h1>{% block h1 %}{{ page_title }}{% endblock %}</h1><p class="sub">{% block sub %}{% endblock %}</p></div>
    <div class="who"><img src="{{ user_avatar }}" alt=""><span>{{ user_name }}</span><form method="post" action="/logout">{{ csrf_field() }}<button class="btn quiet sm">Log out</button></form></div></header>
  {% if flash %}<div class="toast {{ 'ok' if flash[0] else 'bad' }}" role="status"><span>{{ flash[1] }}</span>{% if flash[2] %}<a href="{{ flash[2] }}" target="_blank" rel="noopener">Open in Discord</a>{% endif %}<button type="button" class="x" aria-label="Dismiss">×</button></div>{% endif %}
  <main>{% block content %}{% endblock %}</main>
</div>

<dialog id="ai-modal" aria-labelledby="ai-title">
  <div class="dlg-h"><h2 id="ai-title">Write with AI</h2><button type="button" id="ai-close" aria-label="Close">×</button></div>
  <div class="dlg-b">
    <div class="split">
      <div class="field"><label for="ai-kind">What are you writing?</label><select id="ai-kind"><option value="announcement">Announcement</option><option value="post">Message</option><option value="sticky">Sticky note</option><option value="merch">Merch message</option></select></div>
      <div class="field"><label for="ai-lang">Language</label><select id="ai-lang"><option value="english">English</option><option value="taglish">Taglish</option></select></div>
    </div>
    <div class="field"><span class="lbl">Tone</span><div class="pills"><button type="button" class="pill on" data-tone="friendly and upbeat">Friendly</button><button type="button" class="pill" data-tone="hyped and energetic">Hyped</button><button type="button" class="pill" data-tone="calm and professional">Professional</button><button type="button" class="pill" data-tone="warm and personal">Personal</button><button type="button" class="pill" data-tone="short and to the point">Short</button></div></div>
    <div class="field"><label for="ai-prompt">What should it say?</label><textarea id="ai-prompt" placeholder="e.g. New single out Friday, thank everyone for the support, link in the replies" maxlength="1500"></textarea></div>
    <label class="check hidden" id="ai-rewrite-wrap" style="margin-bottom:16px"><input type="checkbox" id="ai-rewrite" checked><span>Rewrite what I've already typed<small>Gemini improves your current text using your instructions.</small></span></label>
    <div class="actions" style="margin:0 0 16px"><button type="button" class="btn brass" id="ai-go">{{ icon('spark') }} Write it</button><span class="hint">Always read it before posting. Gemini can get details wrong.</span></div>
    <p class="err" id="ai-err" role="alert"></p>
    <div class="field"><label for="ai-out">Result</label><textarea id="ai-out" rows="7" placeholder="Your message appears here. You can edit it before using it."></textarea></div>
    <div class="actions"><button type="button" class="btn plum" id="ai-use" disabled>Use this text</button></div>
  </div>
</dialog>
<script id="boot" type="application/json">{{ boot|tojson }}</script>
<script src="/admin/assets/app.js?v={{ v }}" defer></script>
</body></html>
''',

    'bot.html': r'''{% extends "base.html" %}
{% from "macros.html" import csrf_field, icon with context %}
{% set page_title = "Bot profile" %}
{% block sub %}How the bot looks across Discord. Picture and banner changes are limited by Discord to a few per hour.{% endblock %}
{% block content %}
{% if problem %}<div class="toast bad" style="margin:0 0 18px"><span>{{ problem }}</span></div>{% endif %}
<div class="editor">
  <div>
    <section class="sheet"><h2>Profile picture</h2><p class="hint">PNG, JPG, GIF or WEBP, up to 8 MB. Square works best.</p>
      <form method="post" action="/admin/bot/avatar" enctype="multipart/form-data" class="row">{{ csrf_field() }}
        <div class="field"><input type="file" name="file" accept="image/png,image/jpeg,image/gif,image/webp" data-img-preview="#pv-av" required></div><div class="field" style="flex:0 0 auto"><button class="btn brass">Update picture</button></div></form></section>
    <section class="sheet"><h2>Banner</h2><p class="hint">Wide images look best (about 600 × 240). Discord may require a boosted or verified bot to show banners.</p>
      <form method="post" action="/admin/bot/banner" enctype="multipart/form-data" class="row">{{ csrf_field() }}
        <div class="field"><input type="file" name="file" accept="image/png,image/jpeg,image/gif,image/webp" data-img-preview="#pv-banner" required></div><div class="field" style="flex:0 0 auto"><button class="btn brass">Update banner</button></div></form>
      {% if prof.banner %}<form method="post" action="/admin/bot/banner/remove" data-confirm="Remove the banner?" style="margin-top:6px">{{ csrf_field() }}<button class="btn danger sm">Remove banner</button></form>{% endif %}</section>
    <form class="sheet" method="post" action="/admin/bot/bio">{{ csrf_field() }}<h2>Bio</h2><p class="hint">The “About me” text on the bot's profile.</p>
      <div class="field"><textarea name="bio" rows="5" data-count="400" data-mirror="#pv-bio" maxlength="400">{{ prof.bio }}</textarea><span class="counter"></span></div>
      <div class="actions"><button class="btn brass">Save bio</button></div></form>
    <form class="sheet" method="post" action="/admin/bot/ai">{{ csrf_field() }}<h2>AI writing helper</h2>
      <p class="hint">{% if ai_ready %}<span class="chip live">Gemini connected</span> Model: <code>{{ model }}</code>{% else %}<span class="chip paused">Not connected</span> Add <code>GEMINI_API_KEY</code> in Render → Environment, then redeploy.{% endif %}</p>
      <div class="field" style="margin-top:14px"><label for="ctx">What should Gemini know about the band?</label><textarea id="ctx" name="context" rows="7" data-count="1500">{{ ai_context }}</textarea><span class="counter"></span>
        <p class="hint">Names, release dates, merch details, how you like to sound. Gemini reads this every time it writes. It only knows what you put here.</p></div>
      <div class="actions"><button class="btn brass">Save details</button></div></form>
  </div>
  <div class="pv-col"><div class="pcard"><div class="banner" id="pv-banner" style="{% if prof.banner %}background-image:url('{{ prof.banner }}'){% endif %}"></div>
      <img class="av" id="pv-av" src="{{ prof.avatar or boot.bot_avatar }}" alt=""><div class="pb"><h3>{{ prof.name }}</h3><div class="about"><b>About me</b><span id="pv-bio">{{ prof.bio or ' ' }}</span></div></div></div>
    <p class="pvnote">A preview of the bot's profile card.</p></div>
</div>
{% endblock %}
''',

    'denied.html': r'''{% from "macros.html" import tds_door %}<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>No access · The Door Stoppers</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='-14 -14 302 438'%3E%3Crect x='-14' y='-14' width='302' height='438' rx='40' fill='%231A1521'/%3E%3Cg fill='none' stroke='%23F4B63F' stroke-width='11'%3E%3Crect x='4.5' y='4.5' width='265' height='401'/%3E%3Crect x='59' y='52' width='158' height='140'/%3E%3Cpath d='M59 52L217 192M217 52L59 192'/%3E%3Crect x='59' y='217' width='158' height='140'/%3E%3Cpath d='M59 217L217 357M217 217L59 357'/%3E%3Ccircle cx='243' cy='205' r='13'/%3E%3C/g%3E%3C/svg%3E">
<link rel="stylesheet" href="/admin/assets/app.css?v={{ v }}"></head>
<body class="login"><div class="scene closed">
  <div class="doorway" role="img" aria-label="A closed door" style="width:min(70vw,260px)">
    <div class="room"></div>
    <div class="leaf">{{ tds_door("", true, "#000") }}</div>
  </div>
  <h1 style="font-size:30px;text-align:center">This door is locked</h1>
  <p class="note">You're signed in as <b>{{ name }}</b>, but this account isn't on the approved list.<br>If you should have access, send an admin your Discord ID:<br><span class="deny-id">{{ uid }}</span></p>
  <form method="post" action="/logout"><input type="hidden" name="csrf" value="{{ csrf }}"><button class="btn plum">Sign out</button></form>
</div></body></html>
''',

    'login.html': r'''{% from "macros.html" import tds_door %}<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Sign in · The Door Stoppers</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='-14 -14 302 438'%3E%3Crect x='-14' y='-14' width='302' height='438' rx='40' fill='%231A1521'/%3E%3Cg fill='none' stroke='%23F4B63F' stroke-width='11'%3E%3Crect x='4.5' y='4.5' width='265' height='401'/%3E%3Crect x='59' y='52' width='158' height='140'/%3E%3Cpath d='M59 52L217 192M217 52L59 192'/%3E%3Crect x='59' y='217' width='158' height='140'/%3E%3Cpath d='M59 217L217 357M217 217L59 357'/%3E%3Ccircle cx='243' cy='205' r='13'/%3E%3C/g%3E%3C/svg%3E">
<link rel="stylesheet" href="/admin/assets/app.css?v={{ v }}"></head>
<body class="login"><div class="scene">
  <div class="doorway" role="img" aria-label="A door opening">
    <div class="room">
      <h1>The Door Stoppers</h1>
      {% if disabled %}<p>The dashboard isn't set up yet.</p>{% else %}<p>Band admins only. Sign in with the Discord account you use for the server.</p>
      <a class="btn brass lg" href="/login">Continue with Discord</a>{% endif %}
    </div>
    <div class="leaf">{{ tds_door("", true, "#000") }}</div>
  </div>
  {% if disabled %}<p class="note">Add <code>DISCORD_CLIENT_ID</code>, <code>DISCORD_CLIENT_SECRET</code> and <code>SESSION_SECRET</code> in Render → Environment, then redeploy.</p>{% endif %}
</div></body></html>
''',

    'macros.html': r'''{% macro tds_door(cls='', frame=true, fill='none') %}<svg class="tdsdoor {{ cls }}" viewBox="0 0 274 410" aria-hidden="true" focusable="false"><g fill="none" stroke="currentColor" stroke-width="9" stroke-linejoin="miter">{% if frame %}<rect x="4.5" y="4.5" width="265" height="401" fill="{{ fill }}"/>{% endif %}<rect x="59" y="52" width="158" height="140"/><path d="M59 52L217 192M217 52L59 192"/><rect x="59" y="217" width="158" height="140"/><path d="M59 217L217 357M217 217L59 357"/><circle cx="243" cy="205" r="12"/></g></svg>{% endmacro %}
{% macro csrf_field() %}<input type="hidden" name="csrf" value="{{ csrf }}">{% endmacro %}

{% macro icon(name) %}<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">{% if name == 'home' %}<path d="M5 21V8a7 7 0 0 1 14 0v13"/><path d="M3 21h18"/><circle cx="15.5" cy="14.5" r=".9" fill="currentColor"/>{% elif name == 'merch' %}<path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>{% elif name == 'pin' %}<path d="M12 17v5"/><path d="M8 3h8l-1 6 3 4H6l3-4-1-6z"/>{% elif name == 'send' %}<path d="M21 3 10 14"/><path d="M21 3l-7 18-4-7-7-4 18-7z"/>{% elif name == 'people' %}<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.5"/><path d="M17 14.5a5 5 0 0 1 4 5"/>{% elif name == 'bell' %}<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4l2-2z"/><path d="M10 21a2 2 0 0 0 4 0"/>{% elif name == 'bot' %}<rect x="4" y="8" width="16" height="11" rx="3"/><path d="M12 8V5"/><circle cx="12" cy="3.8" r="1"/><circle cx="9" cy="13.5" r="1" fill="currentColor"/><circle cx="15" cy="13.5" r="1" fill="currentColor"/>{% elif name == 'spark' %}<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z"/><path d="M19 17l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7.7-2z"/>{% endif %}</svg>{% endmacro %}

{% macro channel_select(name, channels, selected='', empty=None, id=None) %}
<select name="{{ name }}"{% if id %} id="{{ id }}"{% endif %}>
{%- if empty %}<option value="">{{ empty }}</option>{% endif %}
{%- set ns = namespace(g=None, open=false) %}
{%- for c in channels %}
{%- if c.group != ns.g %}{% if ns.open %}</optgroup>{% endif %}<optgroup label="{{ c.group }}">{% set ns.g = c.group %}{% set ns.open = true %}{% endif %}
<option value="{{ c.id }}"{% if c.id == (selected|string) %} selected{% endif %}>{{ c.label }}</option>
{%- endfor %}{% if ns.open %}</optgroup>{% endif %}
</select>
{% endmacro %}

{% macro style_select(name, value) %}
<select name="{{ name }}">
{% for k, label in [('primary','Blurple'),('success','Green'),('danger','Red'),('secondary','Grey')] %}<option value="{{ k }}"{% if value == k %} selected{% endif %}>{{ label }}</option>{% endfor %}
</select>
{% endmacro %}

{% macro color_field(name, label, value) %}
<div class="field"><label>{{ label }}</label><div class="colorfield"><input type="color" name="{{ name }}" value="{{ value or '#FFFF00' }}"><code>{{ (value or '#FFFF00')|upper }}</code></div></div>
{% endmacro %}

{% macro image_field(name, label, value, img_map, can_upload) %}
<div class="field"><label>{{ label }}</label>
<div class="imgfield"><div class="line"><input type="text" name="{{ name }}" value="{{ value or '' }}" placeholder="{{ 'Paste an image link, or upload one' if can_upload else 'Paste an image link (https://…)' }}" autocomplete="off">
{% if can_upload %}<button type="button" class="btn ghost upl">Upload</button><input type="file" accept="image/png,image/jpeg,image/gif,image/webp" class="hidden">{% endif %}</div>
<img class="thumb hidden" alt="" src="{{ img_map.get(value, value) if value else '' }}"></div>
{% if not can_upload %}<p class="hint">To upload images from here, set ASSET_CHANNEL_ID in Render (a private channel the bot can post in).</p>{% endif %}</div>
{% endmacro %}

{% macro ai_button(target, kind, limit) %}<button type="button" class="btn ghost sm ai-btn" data-ai="#{{ target }}" data-kind="{{ kind }}" data-limit="{{ limit }}">{{ icon('spark') }} Write with AI</button>{% endmacro %}

{% macro door(kind, form_id, title='Live preview') %}
<div class="door" data-pv data-kind="{{ kind }}" data-form="#{{ form_id }}"><div class="door-head"><i></i>{{ title }}</div><div class="dc"></div><i class="knob"></i></div>
{% endmacro %}
''',

    'members.html': r'''{% extends "base.html" %}
{% from "macros.html" import csrf_field, icon with context %}
{% set page_title = "Members & roles" %}
{% block sub %}Find a member, then add or remove roles. Every change is recorded in the server's audit log with your name.{% endblock %}
{% block content %}
<form class="sheet" method="get" action="/admin/members" style="margin-bottom:22px">
  <div class="row"><div class="field"><label for="q">Search</label><input type="search" id="q" name="q" value="{{ q }}" placeholder="Name, username or ID" autocomplete="off"></div>
    <div class="field"><label>Has role</label><select name="role"><option value="">Any role</option>{% for r in roles %}<option value="{{ r.id }}"{% if r.id == role_filter %} selected{% endif %}>{{ r.name }}</option>{% endfor %}</select></div>
    <div class="field" style="flex:0 0 auto"><button class="btn plum">Search</button></div></div>
  <p class="hint" style="margin:0">Roles with admin permission, bot or integration roles, and roles above the bot are locked.</p>
</form>
<div class="sheet">
{% if not members %}<div class="empty" style="border:0"><b>No one found</b>Try a different name, or clear the filter.</div>
{% else %}<p class="hint" style="margin-bottom:6px">Showing {{ members|length }} of {{ total }}{% if total > members|length %}. Narrow the search to see others.{% endif %}</p>
{% for m in members %}
<div class="mrow"><img src="{{ m.avatar }}" alt="">
  <div><h3>{{ m.display }} <small>@{{ m.name }}</small>{% if m.bot %}<span class="chip">Bot</span>{% endif %}</h3>
    <div class="rchips">{% for r in m.roles %}<span class="rchip{{ '' if r.removable else ' locked' }}" style="--rc:{{ r.color }}"><i></i>{{ r.name }}
      {% if r.removable %}<form method="post" action="/admin/members/role">{{ csrf_field() }}<input type="hidden" name="user_id" value="{{ m.id }}"><input type="hidden" name="role_id" value="{{ r.id }}"><input type="hidden" name="action" value="remove"><input type="hidden" name="q" value="{{ q }}"><input type="hidden" name="rf" value="{{ role_filter }}"><button title="Remove {{ r.name }}" aria-label="Remove {{ r.name }}">×</button></form>{% endif %}</span>{% else %}<span class="hint">No roles</span>{% endfor %}</div></div>
  <form class="addrole" method="post" action="/admin/members/role">{{ csrf_field() }}<input type="hidden" name="user_id" value="{{ m.id }}"><input type="hidden" name="action" value="add"><input type="hidden" name="q" value="{{ q }}"><input type="hidden" name="rf" value="{{ role_filter }}">
    <select name="role_id" aria-label="Role to add">{% for r in assignable %}<option value="{{ r.id }}">{{ r.name }}</option>{% endfor %}</select><button class="btn ghost sm">Add role</button></form>
</div>{% endfor %}{% endif %}
</div>
{% endblock %}
''',

    'merch.html': r'''{% extends "base.html" %}
{% from "macros.html" import csrf_field, icon, channel_select, style_select, color_field, image_field, ai_button, door with context %}
{% set page_title = "Merch panel" %}
{% block sub %}Change what buyers see, the buttons they press and the replies they get. Edits apply right away.{% endblock %}
{% block content %}
<div class="tabs" role="tablist">
  <button class="tab" data-tab="panel" role="tab">Panel</button>
  <button class="tab" data-tab="ticket" role="tab">Ticket welcome</button>
  <button class="tab" data-tab="products" role="tab">Items &amp; buttons</button>
  <button class="tab" data-tab="replies" role="tab">Auto replies</button>
  <button class="tab" data-tab="close" role="tab">Close button</button>
</div>

<div class="tabpane" id="tab-panel"><div class="editor">
  <div>
    <form class="sheet" id="f-panel" method="post" action="/admin/merch/panel">{{ csrf_field() }}
      <h2>Public panel</h2><p class="hint">The card people see with the Order button.</p>
      <div class="field"><label for="p-title">Title</label><input type="text" id="p-title" name="title" value="{{ m.panel.title }}" maxlength="256"></div>
      <div class="field"><label for="p-desc">Description</label><textarea id="p-desc" name="description" rows="9" data-count="4000">{{ m.panel.description }}</textarea><span class="counter"></span>{{ ai_button('p-desc', 'merch', 1800) }}<p class="hint">Supports **bold**, *italic*, ~~strike~~ and bullet lists, like Discord.</p></div>
      <div class="split">{{ color_field('color', 'Card color', m.panel.color) }}<div class="field"><label for="p-footer">Footer (optional)</label><input type="text" id="p-footer" name="footer" value="{{ m.panel.footer }}" maxlength="200"></div></div>
      <div class="split">{{ image_field('image', 'Big image', m.panel.image, img_map, can_upload) }}{{ image_field('thumbnail', 'Small image (top right)', m.panel.thumbnail, img_map, can_upload) }}</div>
      <div class="split"><div class="field"><label for="p-bl">Button text</label><input type="text" id="p-bl" name="button_label" value="{{ m.panel.button_label }}" maxlength="80"></div><div class="field"><label>Button color</label>{{ style_select('button_style', m.panel.button_style) }}</div></div>
      <label class="check" style="margin-bottom:18px"><input type="checkbox" name="push" value="1" {% if m.panel_message.message_id %}checked{% endif %}><span>Also update the panel that's posted in Discord<small>{% if m.panel_message.message_id %}Edits the linked panel message.{% else %}Link or publish a panel below first.{% endif %}</small></span></label>
      <div class="actions"><button class="btn brass">Save changes</button></div>
    </form>
    <div class="sheet"><h2>Where it's posted</h2>
      {% if panel_url %}<p class="hint">The bot is tracking a panel message. <a href="{{ panel_url }}" target="_blank" rel="noopener"><b>Open it in Discord</b></a></p>{% else %}<p class="hint">No panel is linked yet. Publish a new one, or link the one you already posted.</p>{% endif %}
      <form method="post" action="/admin/merch/panel/publish" class="row" style="margin-top:12px">{{ csrf_field() }}<div class="field"><label>Publish a new panel in</label>{{ channel_select('channel', channels) }}</div><div class="field" style="flex:0 0 auto"><button class="btn plum">Publish panel</button></div></form>
      <form method="post" action="/admin/merch/panel/update" class="actions" style="margin-bottom:18px">{{ csrf_field() }}<button class="btn ghost" {% if not panel_url %}disabled{% endif %}>Update posted panel</button></form>
      <form method="post" action="/admin/merch/panel/track" class="row">{{ csrf_field() }}<div class="field"><label>Already posted one? Link it</label><input type="text" name="link" placeholder="Paste the message link (right-click it → Copy Message Link)"></div><div class="field" style="flex:0 0 auto"><button class="btn ghost">Link panel</button></div></form>
    </div>
  </div>
  <div class="pv-col">{{ door('panel', 'f-panel', 'What members see') }}<p class="pvnote">Colors, images and text update as you type.</p></div>
</div></div>

<div class="tabpane" id="tab-ticket"><div class="editor">
  <form class="sheet" id="f-ticket" method="post" action="/admin/merch/ticket">{{ csrf_field() }}
    <h2>Ticket welcome</h2><p class="hint">The first message inside a new order ticket, above the item buttons.</p>
    <div class="field"><label for="t-title">Title</label><input type="text" id="t-title" name="title" value="{{ m.ticket.title }}" maxlength="256"></div>
    <div class="field"><label for="t-desc">Message</label><textarea id="t-desc" name="description" rows="9" data-count="4000">{{ m.ticket.description }}</textarea><span class="counter"></span>{{ ai_button('t-desc', 'merch', 1500) }}
      <p class="hint vars">Use <code class="v">{user}</code> to mention the buyer.</p></div>
    {{ color_field('color', 'Card color', m.ticket.color) }}
    <div class="split">{{ image_field('image', 'Big image', m.ticket.image, img_map, can_upload) }}{{ image_field('thumbnail', 'Small image', m.ticket.thumbnail, img_map, can_upload) }}</div>
    <div class="actions"><button class="btn brass">Save changes</button></div>
  </form>
  <div class="pv-col">{{ door('ticket', 'f-ticket', 'Inside a new ticket') }}<p class="pvnote">The item buttons come from the “Items &amp; buttons” tab.</p></div>
</div></div>

<div class="tabpane" id="tab-products">
  <p class="hint" style="margin:-8px 0 20px;max-width:70ch">Each item is a button in the ticket. When a buyer presses it, they get the reply from the “Auto replies” tab with this item's name, price, note and images filled in.</p>
  {% for p in m.products %}
  <div class="stub">
    <div class="body">
      <h3><span>{{ p.label }}</span><span class="reorder">
        <form method="post" action="/admin/merch/product/move">{{ csrf_field() }}<input type="hidden" name="id" value="{{ p.id }}"><input type="hidden" name="dir" value="up"><button title="Move up" aria-label="Move up"{% if loop.first %} disabled{% endif %}>▲</button></form>
        <form method="post" action="/admin/merch/product/move">{{ csrf_field() }}<input type="hidden" name="id" value="{{ p.id }}"><input type="hidden" name="dir" value="down"><button title="Move down" aria-label="Move down"{% if loop.last %} disabled{% endif %}>▼</button></form></span></h3>
      <form id="f-p-{{ p.id }}" method="post" action="/admin/merch/product">{{ csrf_field() }}<input type="hidden" name="id" value="{{ p.id }}">
        <div class="split"><div class="field"><label>Button text</label><input type="text" name="label" value="{{ p.label }}" maxlength="80"></div><div class="field"><label>Button color</label>{{ style_select('style', p.style) }}</div></div>
        <div class="split"><div class="field"><label>Item name</label><input type="text" name="name" value="{{ p.name }}" maxlength="100"></div><div class="field"><label>Price (Php)</label><input type="text" name="price" value="{{ p.price }}" maxlength="30"></div></div>
        <div class="field"><label>Extra note (optional)</label><input type="text" name="note" value="{{ p.note }}" maxlength="500"><p class="hint">Shown under the price, e.g. a discount line.</p></div>
        <div class="split">{{ image_field('image', 'Big image', p.image, img_map, can_upload) }}{{ image_field('thumbnail', 'Small image', p.thumbnail, img_map, can_upload) }}</div>
        <div class="actions"><button class="btn brass">Save item</button></div>
      </form>
      <form method="post" action="/admin/merch/product/delete" data-confirm="Delete “{{ p.label }}”? Buyers will no longer see this button." style="margin-top:10px">{{ csrf_field() }}<input type="hidden" name="id" value="{{ p.id }}"><button class="btn danger sm">Delete this button</button></form>
    </div>
    <div class="perf"></div>
    <div class="side">{{ door('product', 'f-p-' ~ p.id, 'What the buyer gets') }}</div>
  </div>
  {% endfor %}
  <div class="stub new">
    <div class="body"><h3><span>Add a new button</span></h3>
      <form id="f-p-new" method="post" action="/admin/merch/product">{{ csrf_field() }}<input type="hidden" name="id" value="new">
        <div class="split"><div class="field"><label>Button text</label><input type="text" name="label" placeholder="🎟️ New item" maxlength="80"></div><div class="field"><label>Button color</label>{{ style_select('style', 'primary') }}</div></div>
        <div class="split"><div class="field"><label>Item name</label><input type="text" name="name" placeholder="New item" maxlength="100"></div><div class="field"><label>Price (Php)</label><input type="text" name="price" placeholder="450" maxlength="30"></div></div>
        <div class="field"><label>Extra note (optional)</label><input type="text" name="note" maxlength="500"></div>
        <div class="split">{{ image_field('image', 'Big image', '', img_map, can_upload) }}{{ image_field('thumbnail', 'Small image', '', img_map, can_upload) }}</div>
        <div class="actions"><button class="btn brass">Add button</button></div>
      </form></div>
    <div class="perf"></div>
    <div class="side">{{ door('product', 'f-p-new', 'What the buyer gets') }}</div>
  </div>
</div>

<div class="tabpane" id="tab-replies"><div class="editor">
  <form class="sheet" id="f-reply" method="post" action="/admin/merch/reply">{{ csrf_field() }}
    <h2>Reply after picking an item</h2><p class="hint">Sent when a buyer presses an item button. It's the same template for every item.</p>
    <p class="hint vars" style="margin-bottom:14px">Fill-ins: <code class="v">{product}</code> <code class="v">{price}</code> <code class="v">{note}</code> <code class="v">{user}</code></p>
    <div class="field"><label for="r-msg">Chat message</label><textarea id="r-msg" name="message" rows="5" data-count="2000">{{ m.reply.message }}</textarea><span class="counter"></span>{{ ai_button('r-msg', 'merch', 800) }}<p class="hint">Keep <code class="v">You selected: **{product}**</code> in here. The archive uses it to log which item was ordered.</p></div>
    <div class="field"><label for="r-et">Card title</label><input type="text" id="r-et" name="embed_title" value="{{ m.reply.embed_title }}" maxlength="256"></div>
    <div class="field"><label for="r-ed">Card text</label><textarea id="r-ed" name="embed_description" rows="3" data-count="4000">{{ m.reply.embed_description }}</textarea><span class="counter"></span></div>
    {{ color_field('color', 'Card color', m.reply.color) }}
    <div class="split"><div class="field"><label>“Yes” button</label><input type="text" name="yes_label" value="{{ m.reply.yes_label }}" maxlength="80"></div><div class="field"><label>“No” button</label><input type="text" name="no_label" value="{{ m.reply.no_label }}" maxlength="80"></div></div>
    <hr style="border:0;border-top:1px solid var(--line);margin:8px 0 22px">
    <h2>Order form</h2><p class="hint">Sent after the buyer presses “Yes”.</p>
    <div class="field"><label for="r-form">Form message</label><textarea id="r-form" name="form_text" rows="10" data-count="2000">{{ m.form.text }}</textarea><span class="counter"></span>{{ ai_button('r-form', 'merch', 1200) }}
      <p class="hint">Keep the field names (Name:, Email:, Contact Number:, Complete Delivery Address:, Preferred courier:, Mode of Payment:). The archive reads them to fill your Google Sheet.</p></div>
    <div class="actions"><button class="btn brass">Save changes</button></div>
  </form>
  <div class="pv-col">{{ door('reply', 'f-reply', 'What the buyer sees') }}<p class="pvnote">Shown with your first item as the example. Images come from each item.</p></div>
</div></div>

<div class="tabpane" id="tab-close"><div class="editor">
  <form class="sheet" id="f-close" method="post" action="/admin/merch/close">{{ csrf_field() }}
    <h2>When does the close button show up?</h2><p class="hint">Only admins and TDS - Members can press it. Pressing it archives the ticket to Google Drive and Sheets, then deletes the channel.</p>
    {% for key, title, text in [('ticket_open','As soon as the ticket opens','Staff can close it at any time, even before an item is picked.'),('after_select','After the buyer picks an item','Appears once the buyer chooses what they want.'),('after_proceed','After the buyer presses “Yes”','Appears under the order form. This is how it worked before.'),('after_receipt','After the buyer uploads a receipt','Appears when the buyer posts an image in the ticket. Best for closing only paid orders.')] %}
    <label class="opt"><input type="radio" name="when" value="{{ key }}" {% if m.close.when == key %}checked{% endif %}><div><b>{{ title }}</b><span>{{ text }}</span></div></label>{% endfor %}
    <div class="field" style="margin-top:20px"><label>Button text</label><input type="text" name="label" value="{{ m.close.label }}" maxlength="80"></div>
    <div class="field"><label>Message above the button</label><input type="text" name="message" value="{{ m.close.message }}" maxlength="500"><p class="hint">Not used when the button appears under the order form.</p></div>
    <div class="actions"><button class="btn brass">Save changes</button></div>
  </form>
  <div class="pv-col">{{ door('close', 'f-close', 'Inside the ticket') }}</div>
</div></div>
{% endblock %}
''',

    'notifications.html': r'''{% extends "base.html" %}
{% from "macros.html" import csrf_field, icon, channel_select with context %}
{% set page_title = "Notifications" %}
{% block sub %}Alerts for new YouTube videos, TikToks, Facebook and Instagram posts, and Spotify or Apple Music releases. Checked every {{ interval }} minutes.{% endblock %}
{% block content %}
<section class="sheet"><h2>Where alerts go</h2><p class="hint">Feeds set to “Default” follow this channel.</p>
  <form method="post" action="/admin/notifications/channel" class="row">{{ csrf_field() }}<input type="hidden" name="scope" value="default"><div class="field">{{ channel_select('channel', channels, default_id) }}</div><div class="field" style="flex:0 0 auto"><button class="btn brass">Save</button></div></form>
  <form method="post" action="/admin/notifications/channel" class="row" data-confirm="Move every feed to the selected channel?">{{ csrf_field() }}<input type="hidden" name="scope" value="all"><div class="field">{{ channel_select('channel', channels, default_id) }}</div><div class="field" style="flex:0 0 auto"><button class="btn ghost">Set as default and move all feeds here</button></div></form>
</section>
<section class="sheet"><h2>Feeds ({{ feeds|length }})</h2>
{% if not feeds %}<div class="empty"><b>No feeds yet</b>Add your first one below.</div>{% else %}
<div class="scroll"><table class="tbl"><tr><th>Feed</th><th>Source</th><th>Channel</th><th></th></tr>
{% for f in feeds %}<tr><td>{{ f.emoji }} <b>{{ f.name }}</b><br><span class="hint">{{ f.label }}</span></td><td><code>{{ f.target }}</code></td>
  <td><form method="post" action="/admin/notifications/channel">{{ csrf_field() }}<input type="hidden" name="scope" value="{{ f.name }}">{{ channel_select('channel', channels, f.channel_id, 'Default') }}<button class="btn ghost sm">Save</button></form></td>
  <td style="white-space:nowrap"><form method="post" action="/admin/notifications/test">{{ csrf_field() }}<input type="hidden" name="name" value="{{ f.name }}"><button class="btn ghost sm">Send test</button></form>
    <form method="post" action="/admin/notifications/remove" data-confirm="Remove {{ f.name }}?">{{ csrf_field() }}<input type="hidden" name="name" value="{{ f.name }}"><button class="btn danger sm">Remove</button></form></td></tr>{% endfor %}</table></div>{% endif %}
<form method="post" action="/admin/notifications/check" class="actions" style="margin-top:16px">{{ csrf_field() }}<button class="btn plum">Check all feeds now</button></form>
</section>
<section class="sheet"><h2>Add a feed</h2>
  <form method="post" action="/admin/notifications/add">{{ csrf_field() }}
    <div class="row"><div class="field"><label>Platform</label><select name="platform">{% for k, v in platforms %}<option value="{{ k }}">{{ v }}</option>{% endfor %}</select></div>
      <div class="field"><label>Name</label><input type="text" name="name" placeholder="TDS-YT" maxlength="32" required></div>
      <div class="field" style="flex:2 1 280px"><label>Handle, ID or feed link</label><input type="text" name="target" maxlength="300" required></div>
      <div class="field"><label>Channel</label>{{ channel_select('channel', channels, '', 'Default') }}</div></div>
    <div class="actions"><button class="btn brass">Add feed</button></div></form>
  <ul class="hint" style="margin:18px 0 0 18px;padding:0;line-height:1.8"><li>YouTube: <code>@thedoorstoppersPH</code> or the channel link</li><li>TikTok, Facebook, Instagram: paste the feed link made at rss.app. A profile link won't work.</li><li>Spotify and Apple Music: the artist ID or artist link</li><li>Names can't have spaces. Old posts are ignored, only new ones are announced.</li></ul>
</section>
{% endblock %}
''',

    'overview.html': r'''{% extends "base.html" %}
{% from "macros.html" import icon, tds_door with context %}
{% set page_title = "Home" %}
{% block h1 %}Home{% endblock %}
{% block sub %}Everything for {{ guild_name }} in one place.{% endblock %}
{% block content %}
<div class="hello">Hi, {{ user_name.split(' ')[0] }}.</div>
<p>Pick a door to get started.</p>
<div class="stats">
  <div><b>{{ members }}</b><span>members in the server</span></div>
  <div><b>{{ latency if latency is not none else '–' }}{% if latency is not none %}<small style="font-size:15px"> ms</small>{% endif %}</b><span>bot response time</span></div>
  <div><b>{{ products }}</b><span>merch buttons</span></div>
  <div><b>{{ stickies }}</b><span>live sticky messages</span></div>
  <div><b>{{ feeds }}</b><span>notification feeds</span></div>
</div>
<div class="doors">
  <a class="dtile" href="/admin/merch" style="--dc:#F4B63F"><span class="dg"><i class="hole"></i>{{ tds_door("lf", true, "#fff") }}</span><b>Merch panel</b><span>Buttons, replies, images, colors</span></a>
  <a class="dtile" href="/admin/stickies" style="--dc:#E8576B"><span class="dg"><i class="hole"></i>{{ tds_door("lf", true, "#fff") }}</span><b>Sticky messages</b><span>Silent notes that stay at the bottom</span></a>
  <a class="dtile" href="/admin/send" style="--dc:#2FA6A0"><span class="dg"><i class="hole"></i>{{ tds_door("lf", true, "#fff") }}</span><b>Send a message</b><span>Text, images and video, anywhere</span></a>
  <a class="dtile" href="/admin/members" style="--dc:#7B61D9"><span class="dg"><i class="hole"></i>{{ tds_door("lf", true, "#fff") }}</span><b>Members &amp; roles</b><span>Find someone and change their roles</span></a>
  <a class="dtile" href="/admin/notifications" style="--dc:#3E8EDE"><span class="dg"><i class="hole"></i>{{ tds_door("lf", true, "#fff") }}</span><b>Notifications</b><span>YouTube, TikTok, Facebook, Instagram, music</span></a>
  <a class="dtile" href="/admin/bot" style="--dc:#4DAA6A"><span class="dg"><i class="hole"></i>{{ tds_door("lf", true, "#fff") }}</span><b>Bot profile</b><span>Picture, banner, bio and the AI helper</span></a>
</div>
<section class="sheet" style="max-width:720px"><h2>Setup check</h2><p class="hint">Things that make the dashboard work better.</p>
<ul class="todo">{% for c in checks %}<li class="{{ 'yes' if c.ok else 'no' }}"><span class="mk">{{ '✓' if c.ok else '' }}</span><div><b>{{ c.label }}</b>{% if not c.ok %}<small>{{ c.hint }} <a href="{{ c.href }}">Open</a></small>{% else %}<small>All set.</small>{% endif %}</div></li>{% endfor %}</ul></section>
{% endblock %}
''',

    'send.html': r'''{% extends "base.html" %}
{% from "macros.html" import csrf_field, icon, channel_select, color_field, ai_button, door with context %}
{% set page_title = "Send a message" %}
{% block sub %}Post as the bot in any channel. Add images or videos if you like.{% endblock %}
{% block content %}
<div class="editor">
  <form class="sheet" id="f-send" method="post" action="/admin/send" enctype="multipart/form-data">{{ csrf_field() }}
    <div class="split">
      <div class="field"><label>Send to</label>{{ channel_select('channel', channels) }}</div>
      <div class="field"><label>Ping a role (optional)</label>
        <select name="ping_role"><option value="">Don't ping anyone</option>{% for r in roles %}<option value="{{ r.id }}">{{ r.name }}</option>{% endfor %}</select></div>
    </div>
    <div class="field"><span class="lbl">Format</span>
      <div class="pills"><label class="check"><input type="radio" name="mode" value="plain" checked><span>Plain message</span></label>
      <label class="check" style="margin-left:18px"><input type="radio" name="mode" value="embed"><span>Card with a color bar</span></label></div></div>
    <div class="field" data-when="mode:embed"><label>Card title</label><input type="text" name="title" maxlength="256"></div>
    <div class="field"><label for="m-content">Message</label><textarea id="m-content" name="content" rows="9" data-count="2000" placeholder="Write your message…"></textarea><span class="counter"></span>{{ ai_button('m-content', 'announcement', 1800) }}</div>
    <div data-when="mode:embed">{{ color_field('color', 'Card color', '#FFFF00') }}<div class="field"><label>Card image link (optional)</label><input type="text" name="image" placeholder="https://…" autocomplete="off"><p class="hint">Or just attach an image below and the first one is used.</p></div></div>
    <div class="field"><label>Images &amp; videos</label>
      <label class="drop" style="display:block;border:2px dashed var(--lineStrong);border-radius:14px;padding:22px;text-align:center;cursor:pointer;background:var(--soft)">
        <input type="file" name="files" multiple accept="image/*,video/*,.gif,.pdf,.zip,.txt" class="hidden"><b>Drop files here or click to choose</b>
        <div class="hint">Up to 10 files, {{ limit_mb }} MB each in this server.</div><div class="drop-list hint" style="margin-top:8px;color:var(--ink)"></div></label></div>
    <label class="check" style="margin-bottom:18px"><input type="checkbox" name="silent" value="1"><span>Send silently<small>No notification sound or badge for members.</small></span></label>
    <div class="actions"><button class="btn brass">Send message</button></div>
  </form>
  <div class="pv-col">{{ door('send', 'f-send', 'How it will look') }}<p class="pvnote">Only the role you pick gets pinged. @everyone and @here are blocked.</p></div>
</div>
{% endblock %}
''',

    'stickies.html': r'''{% extends "base.html" %}
{% from "macros.html" import csrf_field, icon, channel_select, color_field, image_field, ai_button, door with context %}
{% set page_title = "Sticky messages" %}
{% block sub %}A note that stays at the bottom of a channel. The bot re-posts it silently after new messages, so nobody gets pinged.{% endblock %}
{% block content %}
{% set found = stickies|selectattr('id', 'equalto', edit)|list if edit else [] %}
{% set cur = found[0] if found else none %}
<div class="editor">
  <form class="sheet" id="f-sticky" method="post" action="/admin/stickies/save">{{ csrf_field() }}
    <h2>{{ 'Edit sticky message' if cur else 'New sticky message' }}</h2><p class="hint">{{ 'Changes repost it right away.' if cur else 'It posts as soon as you save.' }}</p>
    <input type="hidden" name="id" value="{{ cur.id if cur else '' }}">
    <div class="field"><label>Channel</label>{{ channel_select('channel', channels, cur.channel_id if cur else '') }}<p class="hint">Each channel can have one sticky message.</p></div>
    <div class="field"><span class="lbl">Style</span>
      <div class="pills" role="radiogroup">
        <label class="check"><input type="radio" name="mode" value="text" {% if not cur or cur.mode != 'embed' %}checked{% endif %}><span>Plain text</span></label>
        <label class="check" style="margin-left:18px"><input type="radio" name="mode" value="embed" {% if cur and cur.mode == 'embed' %}checked{% endif %}><span>Card with a color bar</span></label></div></div>
    <div class="field" data-when="mode:embed"><label>Title</label><input type="text" name="title" value="{{ cur.title if cur else '' }}" maxlength="256"></div>
    <div class="field"><label for="s-content">Message</label><textarea id="s-content" name="content" rows="7" data-count="1900">{{ cur.content if cur else '' }}</textarea><span class="counter"></span>{{ ai_button('s-content', 'sticky', 600) }}</div>
    <div data-when="mode:embed">{{ color_field('color', 'Card color', cur.color if cur else '#FFFF00') }}{{ image_field('image', 'Image (optional)', cur.image if cur else '', img_map, can_upload) }}</div>
    <label class="check" style="margin-bottom:18px"><input type="checkbox" name="enabled" value="1" {% if not cur or cur.enabled %}checked{% endif %}><span>Live<small>Turn off to pause it without deleting.</small></span></label>
    <div class="actions"><button class="btn brass">{{ 'Save and repost' if cur else 'Save and post' }}</button>{% if cur %}<a class="btn ghost" href="/admin/stickies">Cancel</a>{% endif %}</div>
  </form>
  <div class="pv-col">{{ door('sticky', 'f-sticky', 'At the bottom of the channel') }}<p class="pvnote">The small 📌 Sticky tag lets the bot find its own note. Members only see it quietly.</p></div>
</div>

<h2 style="margin:38px 0 14px;font-size:22px">Your sticky messages</h2>
{% if not stickies %}<div class="empty"><b>No sticky messages yet</b>Add one above, for example your rules or a “start here” note.</div>
{% else %}<div class="list">{% for s in stickies %}
  <div class="item"><div><h3>#{{ s.channel_name }} <span class="chip {{ 'live' if s.enabled else 'paused' }}">{{ 'Live' if s.enabled else 'Paused' }}</span><span class="chip">{{ 'Card' if s.mode == 'embed' else 'Text' }}</span></h3><p>{{ s.content }}</p></div>
    <div class="acts"><a class="btn ghost sm" href="/admin/stickies?edit={{ s.id }}">Edit</a>
      <form method="post" action="/admin/stickies/repost">{{ csrf_field() }}<input type="hidden" name="id" value="{{ s.id }}"><button class="btn ghost sm"{% if not s.enabled %} disabled{% endif %}>Repost</button></form>
      <form method="post" action="/admin/stickies/delete" data-confirm="Delete this sticky message and remove it from #{{ s.channel_name }}?">{{ csrf_field() }}<input type="hidden" name="id" value="{{ s.id }}"><button class="btn danger sm">Delete</button></form></div></div>
{% endfor %}</div>{% endif %}
{% endblock %}
''',

}
