(function() {
    var chartType = "__CHART_TYPE__";
    var labels = __LABELS__;
    var opens  = __OPENS__;
    var highs  = __HIGHS__;
    var lows   = __LOWS__;
    var closes = __CLOSES__;
    var counts = __COUNTS__;
    var ap = __AP__;
    var avg = __AVG__;
    var nn = chartType === 'line' ? ap.length : labels.length;
    if (nn < 1) return;

    var cv = document.getElementById("__CHART_ID__");
    if (!cv) return;
    var tipEl = document.getElementById("__CHART_ID___tip");
    var ovCv = document.getElementById("__CHART_ID___ov");

    var dpr = window.devicePixelRatio || 1;
    var W = cv.clientWidth, H = cv.clientHeight;
    cv.width = W * dpr; cv.height = H * dpr;
    ovCv.width = W * dpr; ovCv.height = H * dpr;
    ovCv.style.width = W + "px"; ovCv.style.height = H + "px";

    var ctx = cv.getContext("2d");
    ctx.scale(dpr, dpr);
    var oc = ovCv.getContext("2d");

    var pad = {t: 20, r: 20, b: 52, l: 52};
    var gW = W - pad.l - pad.r, gH = H - pad.t - pad.b;

    var allMin = Infinity, allMax = -Infinity;
    if (chartType === 'line') {
        for (var i = 0; i < nn; i++) {
            if (ap[i] < allMin) allMin = ap[i];
            if (ap[i] > allMax) allMax = ap[i];
        }
    } else {
        for (var i = 0; i < nn; i++) {
            if (lows[i] < allMin) allMin = lows[i];
            if (highs[i] > allMax) allMax = highs[i];
        }
    }
    var rng = allMax - allMin || 1;
    allMin -= rng * 0.08;
    allMax += rng * 0.08;

    function xOfLine(i) { return pad.l + (i / Math.max(nn - 1, 1)) * gW; }
    function yOf(v) { return pad.t + gH - (v - allMin) / (allMax - allMin) * gH; }

    var candleSpace = gW / nn;
    var candleW = Math.max(3, Math.min(candleSpace * 0.6, 30));
    function xCenter(i) { return pad.l + candleSpace * (i + 0.5); }

    ctx.fillStyle = "#1a1a2e";
    ctx.fillRect(0, 0, W, H);

    ctx.strokeStyle = "#2a2a3e";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#666";
    ctx.font = "11px -apple-system, sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (var i = 0; i <= 5; i++) {
        var v = allMin + (allMax - allMin) * (i / 5);
        var y = yOf(v);
        ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
        ctx.fillText(Math.round(v), pad.l - 8, y);
    }

    var avgY = yOf(avg);
    ctx.save();
    ctx.strokeStyle = "#ff9800";
    ctx.lineWidth = 1;
    ctx.setLineDash([6, 4]);
    ctx.beginPath(); ctx.moveTo(pad.l, avgY); ctx.lineTo(W - pad.r, avgY); ctx.stroke();
    ctx.restore();
    ctx.fillStyle = "#ff9800";
    ctx.font = "10px -apple-system, sans-serif";
    ctx.textAlign = "right";
    ctx.fillText("均值:" + avg, W - pad.r - 4, avgY - 8);

    ctx.fillStyle = "#666";
    ctx.font = "10px -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    if (chartType === 'line') {
        var labelStep = Math.max(1, Math.floor(nn / 8));
        for (var i = 0; i < nn; i += labelStep) {
            ctx.save();
            ctx.translate(xOfLine(i), H - pad.b + 8);
            ctx.rotate(0.4);
            ctx.fillText(labels[i], 0, 0);
            ctx.restore();
        }
    } else {
        var labelStep = Math.max(1, Math.floor(nn / 12));
        for (var i = 0; i < nn; i += labelStep) {
            ctx.fillText(labels[i], xCenter(i), H - pad.b + 8);
        }
    }

    if (chartType === 'line') {
        var grad = ctx.createLinearGradient(0, pad.t, 0, pad.t + gH);
        grad.addColorStop(0, "rgba(100,120,160,0.18)");
        grad.addColorStop(1, "rgba(100,120,160,0.02)");
        ctx.beginPath();
        ctx.moveTo(xOfLine(0), yOf(ap[0]));
        for (var i = 1; i < nn; i++) {
            if (nn < 30) {
                var x0 = xOfLine(i-1), y0 = yOf(ap[i-1]), x1 = xOfLine(i), y1 = yOf(ap[i]);
                var cpx = (x0 + x1) / 2;
                ctx.bezierCurveTo(cpx, y0, cpx, y1, x1, y1);
            } else {
                ctx.lineTo(xOfLine(i), yOf(ap[i]));
            }
        }
        ctx.lineTo(xOfLine(nn-1), pad.t + gH);
        ctx.lineTo(xOfLine(0), pad.t + gH);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();

        ctx.lineWidth = 2;
        ctx.lineJoin = "round";
        for (var i = 1; i < nn; i++) {
            ctx.beginPath();
            ctx.moveTo(xOfLine(i-1), yOf(ap[i-1]));
            var segmentColor = ap[i] >= ap[i-1] ? "#ef5350" : "#26a69a";
            ctx.strokeStyle = segmentColor;
            if (nn < 30) {
                var x0 = xOfLine(i-1), y0 = yOf(ap[i-1]), x1 = xOfLine(i), y1 = yOf(ap[i]);
                var cpx = (x0 + x1) / 2;
                ctx.bezierCurveTo(cpx, y0, cpx, y1, x1, y1);
            } else {
                ctx.lineTo(xOfLine(i), yOf(ap[i]));
            }
            ctx.stroke();
        }
        if (nn < 60) {
            for (var i = 0; i < nn; i++) {
                ctx.beginPath();
                ctx.arc(xOfLine(i), yOf(ap[i]), 3.5, 0, Math.PI * 2);
                var dotColor = (i > 0 && ap[i] < ap[i-1]) ? "#26a69a" : "#ef5350";
                ctx.fillStyle = dotColor;
                ctx.fill();
                ctx.strokeStyle = "#1a1a2e";
                ctx.lineWidth = 1.5;
                ctx.stroke();
            }
        }
    } else {
        for (var i = 0; i < nn; i++) {
            var cx = xCenter(i);
            var o = opens[i], h = highs[i], l = lows[i], c = closes[i];
            var isUp = c > o;
            var isDown = c < o;
            var isFlat = c === o;
            var color = isFlat ? "#888" : (isUp ? "#ef5350" : "#26a69a");

            ctx.strokeStyle = color;
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(cx, yOf(h));
            ctx.lineTo(cx, yOf(l));
            ctx.stroke();

            var bodyTop = yOf(Math.max(o, c));
            var bodyBot = yOf(Math.min(o, c));
            var bodyH = Math.max(bodyBot - bodyTop, 1);

            if (isUp || isDown) {
                ctx.fillStyle = color;
                ctx.fillRect(cx - candleW / 2, bodyTop, candleW, bodyH);
            } else {
                ctx.beginPath();
                ctx.moveTo(cx - candleW / 2, yOf(o));
                ctx.lineTo(cx + candleW / 2, yOf(o));
                ctx.stroke();
            }
        }

        function drawMA(days, maColor) {
            if (nn < days) return;
            ctx.beginPath();
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = maColor;
            var started = false;
            for (var i = days - 1; i < nn; i++) {
                var sum = 0;
                for (var j = 0; j < days; j++) sum += closes[i - j];
                var maVal = sum / days;
                var x = xCenter(i), y = yOf(maVal);
                if (!started) { ctx.moveTo(x, y); started = true; }
                else { ctx.lineTo(x, y); }
            }
            ctx.stroke();
        }
        drawMA(5, "#ffeb3b");
        drawMA(10, "#e91e63");
    }

    cv.addEventListener("mousemove", function(e) {
        var rect = cv.getBoundingClientRect();
        var mx_ = e.clientX - rect.left;
        var my_ = e.clientY - rect.top;

        oc.setTransform(1, 0, 0, 1, 0, 0);
        oc.clearRect(0, 0, ovCv.width, ovCv.height);

        if (mx_ < pad.l || mx_ > W - pad.r || my_ < pad.t || my_ > pad.t + gH) {
            tipEl.style.display = "none";
            return;
        }

        oc.scale(dpr, dpr);

        if (chartType === 'line') {
            var ratio = (mx_ - pad.l) / gW;
            var idx = Math.round(ratio * (nn - 1));
            idx = Math.max(0, Math.min(nn - 1, idx));
            var px = xOfLine(idx), py = yOf(ap[idx]);

            oc.strokeStyle = "rgba(255,255,255,0.18)";
            oc.lineWidth = 1;
            oc.setLineDash([4, 3]);
            oc.beginPath(); oc.moveTo(px, pad.t); oc.lineTo(px, pad.t + gH); oc.stroke();
            oc.beginPath(); oc.moveTo(pad.l, py); oc.lineTo(W - pad.r, py); oc.stroke();
            oc.setLineDash([]);

            oc.beginPath(); oc.arc(px, py, 6, 0, Math.PI * 2);
            oc.fillStyle = "rgba(100,181,246,0.3)"; oc.fill();
            oc.beginPath(); oc.arc(px, py, 4, 0, Math.PI * 2);
            oc.fillStyle = "#64b5f6"; oc.fill();
            oc.strokeStyle = "#fff"; oc.lineWidth = 2; oc.stroke();
            oc.setTransform(1, 0, 0, 1, 0, 0);

            var diff = idx > 0 ? (ap[idx] - ap[idx - 1]) : 0;
            var isUp = diff >= 0;
            var dc = isUp ? "#ef5350" : "#26a69a";
            var ds = (isUp ? "+" : "") + diff;
            tipEl.innerHTML = '<div style="color:#888;margin-bottom:4px;font-weight:600">' + labels[idx] + '</div>'
                + '<div>体力: <b style="color:#64b5f6">' + ap[idx] + '</b></div>'
                + '<div>单次变化: <b style="color:' + dc + '">' + ds + '</b></div>';
        } else {
            var idx = Math.floor((mx_ - pad.l) / candleSpace);
            idx = Math.max(0, Math.min(nn - 1, idx));
            var cx = xCenter(idx);

            oc.strokeStyle = "rgba(255,255,255,0.18)";
            oc.lineWidth = 1;
            oc.setLineDash([4, 3]);
            oc.beginPath(); oc.moveTo(cx, pad.t); oc.lineTo(cx, pad.t + gH); oc.stroke();
            oc.beginPath(); oc.moveTo(pad.l, my_); oc.lineTo(W - pad.r, my_); oc.stroke();
            oc.setLineDash([]);

            oc.strokeStyle = "#fff";
            oc.lineWidth = 1;
            oc.globalAlpha = 0.15;
            oc.fillStyle = "#fff";
            oc.fillRect(cx - candleW / 2 - 2, pad.t, candleW + 4, gH);
            oc.globalAlpha = 1.0;
            oc.setTransform(1, 0, 0, 1, 0, 0);

            var o = opens[idx], h = highs[idx], l = lows[idx], c_ = closes[idx];
            var chg = c_ - o;
            var chgPct = o !== 0 ? ((chg / o) * 100).toFixed(1) : "0.0";
            var isUp = c_ >= o;
            var dc = isUp ? "#ef5350" : "#26a69a";
            var chgSign = chg >= 0 ? "+" : "";

            var ma5Val = "-";
            if (idx >= 4) {
                var sum5 = 0; for(var j=0; j<5; j++) sum5+=closes[idx-j];
                ma5Val = (sum5/5).toFixed(1);
            }
            var ma10Val = "-";
            if (idx >= 9) {
                var sum10 = 0; for(var j=0; j<10; j++) sum10+=closes[idx-j];
                ma10Val = (sum10/10).toFixed(1);
            }

            tipEl.innerHTML = '<div style="color:#888;margin-bottom:4px;font-weight:600">' + labels[idx] + '</div>'
                + '<div>开盘: <b>' + o + '</b> <span style="margin-left:8px;color:#ffeb3b">MA5(5期平均): ' + ma5Val + '</span></div>'
                + '<div>收盘: <b style="color:' + dc + '">' + c_ + '</b> <span style="margin-left:8px;color:#e91e63">MA10(10期平均): ' + ma10Val + '</span></div>'
                + '<div>最高: <b style="color:#ef5350">' + h + '</b></div>'
                + '<div>最低: <b style="color:#26a69a">' + l + '</b></div>'
                + '<div>涨跌: <b style="color:' + dc + '">' + chgSign + chg + ' (' + chgSign + chgPct + '%)</b></div>'
                + '<div style="color:#666;margin-top:4px">数据点密度: ' + counts[idx] + '</div>';
        }

        tipEl.style.display = "block";
        var tx = (chartType === 'line' ? px : cx) + 18;
        var ty = my_ - 60;
        if (tx + 180 > W) tx = (chartType === 'line' ? px : cx) - 200;
        if (ty < 8) ty = my_ + 18;
        tipEl.style.left = tx + "px";
        tipEl.style.top = ty + "px";
    });

    cv.addEventListener("mouseleave", function() {
        tipEl.style.display = "none";
        oc.setTransform(1, 0, 0, 1, 0, 0);
        oc.clearRect(0, 0, ovCv.width, ovCv.height);
    });
})();
