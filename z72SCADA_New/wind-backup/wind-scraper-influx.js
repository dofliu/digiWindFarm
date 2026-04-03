// Wind Scraper v7.0 - InfluxDB 備份版
// 用法：在風機監控系統的瀏覽器 Console 執行

(function () {
    // ========== 設定區 ==========
    const INFLUXDB_URL = 'http://localhost:8086';
    const INFLUXDB_TOKEN = 'wind-backup-token-2026';
    const INFLUXDB_ORG = 'windpower';
    const INFLUXDB_BUCKET = 'wind_10min';

    const DEVICES = [
        { id: 'TW:ZG:H05', name: 'H05' },
        { id: 'TW:ZG:H06', name: 'H06' },
        { id: 'TW:ZG:H07', name: 'H07' },
        { id: 'TW:ZG:H08', name: 'H08' },
        { id: 'TW:ZG:H09', name: 'H09' },
        { id: 'TW:ZG:H10', name: 'H10' },
        { id: 'TW:ZG:H12', name: 'H12' },
        { id: 'TW:ZG:H13', name: 'H13' },
        { id: 'TW:ZG:H14', name: 'H14' },
        { id: 'TW:ZG:H15', name: 'H15' },
        { id: 'TW:ZG:H16', name: 'H16' },
        { id: 'TW:ZG:H17', name: 'H17' },
        { id: 'TW:ZG:H18', name: 'H18' },
        { id: 'TW:TZ:P04', name: 'P04' }
    ];

    const START_DATE = '2023-01-01';
    const END_DATE = '2025-12-31';
    const INTERVAL = 600; // 10分鐘 = 600秒
    const DELAY_MS = 500;

    // 標籤清單 (id: API用, name: 顯示用)
    const TAGS = [
        // 電網相關
        { id: 'WGDC_PowerFactor', name: '發電機功因' },
        { id: 'WGDC_Analogue_TrfCoreTmp', name: '變壓器中心溫度' },
        { id: 'WGDC_PhsA_V', name: '變壓器電壓1' },
        { id: 'WGDC_PhsA_I', name: '變壓器電流1' },
        { id: 'WGDC_Analogue_TrfPhTmp', name: '變壓器相位溫度' },
        // 發電機
        { id: 'WGEN_Analogue_GnAirTmp1', name: '發電機氣隙溫度01' },
        { id: 'WGEN_Speed', name: '發電機轉速' },
        { id: 'WGEN_Analogue_GnBrgTmp1', name: '發電機軸承溫度01' },
        { id: 'WGEN_Analogue_GnVtgMs', name: '發電機電壓' },
        { id: 'WGEN_Analogue_GnCurMs', name: '發電機電流' },
        { id: 'WGEN_Temp', name: '發電機靜子溫度01' },
        { id: 'WGEN_Temp1', name: '發電機靜子溫度02' },
        // 風電機組
        { id: 'WTUR_ActPower', name: '電網有功功率' },
        { id: 'WTUR_Trip20', name: '緊急跳機訊息01' },
        { id: 'WTUR_Alarm0', name: '警報訊息01' },
        { id: 'WTUR_Info', name: 'PLC控制訊息' },
        { id: 'WTUR_Trip10', name: '一般跳機訊息01' },
        { id: 'WTUR_Trip11', name: '一般跳機訊息02' },
        { id: 'WTUR_RawProduction', name: '有功發電量' },
        { id: 'WTUR_Trip21', name: '緊急跳機訊息02' },
        { id: 'WTUR_Trip22', name: '緊急跳機訊息03' },
        { id: 'WTUR_Trip23', name: '緊急跳機訊息04' },
        { id: 'WTUR_Trip24', name: '緊急跳機訊息05' },
        { id: 'WTUR_Alarm1', name: '警報訊息02' },
        { id: 'WTUR_Alarm2', name: '警報訊息03' },
        { id: 'WTUR_Alarm3', name: '警報訊息04' },
        { id: 'WTUR_Alarm4', name: '警報訊息05' },
        { id: 'WTUR_RawStatus', name: '風力機狀態' },
        // 變頻器
        { id: 'WCNV_Analogue_GnPwrLimCnv', name: '發電機功率限制' },
        { id: 'WCNV_Analogue_CnvGnPwr', name: '變頻器發電機功率' },
        { id: 'WCNV_ActPower', name: '變頻器電網實功率' },
        { id: 'WCNV_ReactPower', name: '變頻器電網虛功率' },
        // 機艙系統
        { id: 'WNAC_WindSpeed', name: '風速即時' },
        { id: 'WNAC_WindDir', name: '風向' },
        { id: 'WNAC_WindSpeed_10m', name: '風速10分鐘平均' },
        { id: 'WNAC_WindSpeed_60s', name: '風速60秒平均' },
        { id: 'WNAC_Analogue_VibMsNacXDir', name: '機艙X方向振動值' },
        { id: 'WNAC_Analogue_VibMsNacYDir', name: '機艙Y方向振動值' },
        { id: 'WNAC_Analogue_AirPress', name: '大氣壓力' },
        // 轉向系統
        { id: 'WYAW_Analogue_YwVn1AlgnAvg5s', name: '轉向Vn1定位5秒' },
        { id: 'WYAW_Analogue_YwVn2AlgnAvg25s', name: '轉向Vn2定位25秒' },
        { id: 'WYAW_Analogue_YwBrkHyPrs', name: '轉向剎車液壓壓力' },
        { id: 'WYAW_Analogue_CabWup', name: '纜線防絞捲' },
        { id: 'WYAW_Analogue_YwVn1AlgnAvg25s', name: '轉向Vn1定位25秒' },
        { id: 'WYAW_Analogue_YwVn2AlgnAvg5s', name: '轉向Vn2定位5秒' },
        { id: 'WYAW_Analogue_YwAlgnAutoOn', name: '轉向定位自動開啟' },
        { id: 'WYAW_Analogue_YwAlgnAutoOff', name: '轉向定位自動關閉' },
        { id: 'WYAW_State_YwBrkSt', name: '轉向剎車狀態' },
        { id: 'WYAW_State_YwSt', name: '轉向系統狀態' },
        // 旋角系統
        { id: 'WROT_Analogue_PtMotCurBl1', name: '葉片1旋角馬達電流' },
        { id: 'WROT_PtBl1', name: '葉片1角度' },
        { id: 'WROT_Analogue_PtMotCurBl2', name: '葉片2旋角馬達電流' },
        { id: 'WROT_PtBl2', name: '葉片2角度' },
        { id: 'WROT_Analogue_PtMotCurBl3', name: '葉片3旋角馬達電流' },
        { id: 'WROT_PtBl3', name: '葉片3角度' },
        { id: 'WROT_Analogue_RotAng', name: '葉輪角度' },
        { id: 'WROT_Speed', name: '葉輪轉速' },
        { id: 'WROT_Analogue_RotSpdMaxVal', name: '葉輪轉速峰值' },
        { id: 'WROT_Analogue_OvrSpdMon', name: '過轉速監控' },
        { id: 'WROT_Analogue_LckngPnPos', name: '鎖緊削位置' },
        // 狀態資訊 - 風電機組
        { id: 'WTUR_Control_Change', name: '控制權切換' },
        { id: 'WTUR_Control_Change_Stop', name: '控制權停止遠端' },
        { id: 'WTUR_Control_Change_Start', name: '控制權啟動遠端' },
        { id: 'WTUR_Control_SrvOff', name: '系統服務SrvOff' },
        { id: 'WTUR_Control_SrvOn', name: '系統服務SrvOn' },
        { id: 'WTUR_Control_LocStpCmd', name: '現場停機' },
        { id: 'WTUR_Control_LocStrCmd', name: '現場啟動' },
        { id: 'WTUR_Control_LocRstCmd', name: '現場重置' },
        { id: 'WTUR_Control_RmtStpCmd', name: '遠端停機' },
        { id: 'WTUR_Control_RmtStrCmd', name: '遠端啟動' },
        { id: 'WTUR_Control_RmtRstCmd', name: '遠端重置' },
        { id: 'WTUR_Control_Local', name: '風機本地控制' },
        // 狀態資訊 - 轉向系統
        { id: 'WYAW_Control_YwManCcw', name: '轉向控制Ccw' },
        { id: 'WYAW_Control_YwManCw', name: '轉向控制Cw' },
        { id: 'WYAW_Control_YwManStop', name: '轉向控制Stop' }
    ];
    // =============================

    const KEY = 'wsp7_progress';
    let P = JSON.parse(localStorage.getItem(KEY) || '{"done":{},"cursor":{}}');
    if (!P.done) P = { done: {}, cursor: {} };

    let R = false, S = false;

    const pad = n => String(n).padStart(2, '0');
    const fmtDate = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

    // 查詢 API
    async function query(deviceId, deviceName, from, to) {
        return new Promise((res, rej) => {
            $.post('/wmc/queryHistory_hisd', {
                tags: TAGS.map(t => deviceId + '|' + t.id),
                tagsCN: TAGS.map(t => deviceName + '|' + t.name),
                fromTime: from,
                toTime: to,
                interval: INTERVAL
            }, res, 'json').fail((xhr, s, e) => {
                if (xhr.status === 401 || xhr.status === 403) {
                    rej(new Error('SESSION_EXPIRED'));
                } else {
                    rej(new Error(s + ': ' + e));
                }
            });
        });
    }

    // 轉換為 InfluxDB Line Protocol
    function toLineProtocol(device, timeArray, datas) {
        const lines = [];
        for (let i = 0; i < timeArray.length; i++) {
            const ts = new Date(timeArray[i].replace(' ', 'T') + '+08:00').getTime() * 1000000; // 納秒
            for (let j = 0; j < datas.length; j++) {
                const val = datas[j].data[i];
                if (val === null || val === undefined || val === '') continue;
                const measurement = datas[j].tag.split('|')[1]; // 取標籤ID
                const numVal = parseFloat(val);
                if (isNaN(numVal)) continue;
                lines.push(`${measurement},device=${device.name} value=${numVal} ${ts}`);
            }
        }
        return lines.join('\n');
    }

    // 寫入 InfluxDB
    async function writeToInflux(lineData) {
        const url = `${INFLUXDB_URL}/api/v2/write?org=${INFLUXDB_ORG}&bucket=${INFLUXDB_BUCKET}&precision=ns`;
        const resp = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': `Token ${INFLUXDB_TOKEN}`,
                'Content-Type': 'text/plain'
            },
            body: lineData
        });
        if (!resp.ok) {
            throw new Error(`InfluxDB write failed: ${resp.status}`);
        }
    }

    function save() { localStorage.setItem(KEY, JSON.stringify(P)); }

    async function processDay(device, dateStr) {
        const from = `${dateStr} 00:00:00`;
        const to = `${dateStr} 23:59:59`;
        const pKey = `${device.name}_${dateStr}`;

        if (P.done[pKey]) return true;

        console.log(`⏳ ${device.name} ${dateStr}...`);
        const t0 = Date.now();

        try {
            const data = await query(device.id, device.name, from, to);
            const sec = ((Date.now() - t0) / 1000).toFixed(1);

            if (data.timeArray?.length) {
                const lineData = toLineProtocol(device, data.timeArray, data.datas);
                await writeToInflux(lineData);
                console.log(`✓ ${device.name} ${dateStr} - ${data.timeArray.length} rows → InfluxDB (${sec}s)`);
            } else {
                console.log(`⚠ ${device.name} ${dateStr} - No data`);
            }

            P.done[pKey] = true;
            save();
            return true;

        } catch (e) {
            if (e.message === 'SESSION_EXPIRED') {
                console.error('🔴 SESSION 已過期！請重新登入');
                S = true;
                return false;
            }
            console.error(`✗ ${device.name} ${dateStr} - ${e.message}`);
            return false;
        }
    }

    async function runDevice(device) {
        const startFrom = P.cursor[device.name] || START_DATE;
        let cur = new Date(startFrom);
        const ed = new Date(END_DATE);
        const totalDays = Math.ceil((ed - new Date(START_DATE)) / 86400000) + 1;
        const doneDays = Math.ceil((cur - new Date(START_DATE)) / 86400000);

        console.log(`${'═'.repeat(40)}`);
        console.log(`🌀 ${device.name} (${doneDays}/${totalDays} 天已完成)`);

        while (cur <= ed && !S) {
            const dateStr = fmtDate(cur);
            const ok = await processDay(device, dateStr);

            if (ok) {
                cur.setDate(cur.getDate() + 1);
                P.cursor[device.name] = fmtDate(cur);
                save();
            } else if (!S) {
                console.log('⏳ 等待 5 秒後重試...');
                await new Promise(r => setTimeout(r, 5000));
            }

            await new Promise(r => setTimeout(r, DELAY_MS));
        }

        if (cur > ed) {
            P.cursor[device.name] = 'DONE';
            save();
        }
        return !S;
    }

    async function run() {
        if (R) { console.log('Already running!'); return; }
        R = true; S = false;

        console.log('═'.repeat(50));
        console.log('🌀 Wind Scraper v7.0 - InfluxDB 備份版');
        console.log(`📦 ${DEVICES.length} 機組 × ${TAGS.length} 標籤`);
        console.log(`📅 ${START_DATE} → ${END_DATE} (10分鐘間隔)`);
        console.log(`💾 寫入 ${INFLUXDB_URL}`);
        console.log('═'.repeat(50));

        for (const device of DEVICES) {
            if (S) break;
            if (P.cursor[device.name] === 'DONE') {
                console.log(`✅ ${device.name} 已完成，跳過`);
                continue;
            }
            await runDevice(device);
        }

        R = false;
        console.log(S ? '⏸ 已暫停' : '🎉 全部完成！');
    }

    window.ws = {
        start: run,
        stop: () => { S = true; console.log('⏸ 正在停止...'); },
        status: () => {
            const totalDays = Math.ceil((new Date(END_DATE) - new Date(START_DATE)) / 86400000) + 1;
            console.log('═'.repeat(40));
            console.log(`📊 進度 (${TAGS.length} 標籤/機組)`);
            DEVICES.forEach(d => {
                const cursor = P.cursor[d.name];
                if (cursor === 'DONE') {
                    console.log(`  ${d.name}: ✅ 完成`);
                } else if (cursor) {
                    const done = Math.ceil((new Date(cursor) - new Date(START_DATE)) / 86400000);
                    const pct = (done / totalDays * 100).toFixed(1);
                    console.log(`  ${d.name}: ${done}/${totalDays} (${pct}%)`);
                } else {
                    console.log(`  ${d.name}: 尚未開始`);
                }
            });
        },
        reset: (name) => {
            if (name) {
                Object.keys(P.done).filter(k => k.startsWith(name + '_')).forEach(k => delete P.done[k]);
                delete P.cursor[name];
                save();
                console.log(`🔄 已重置 ${name}`);
            } else {
                localStorage.removeItem(KEY);
                P = { done: {}, cursor: {} };
                console.log('🔄 已重置全部');
            }
        },
        test: async () => {
            console.log('🧪 測試 InfluxDB 連線...');
            try {
                const resp = await fetch(`${INFLUXDB_URL}/health`);
                const data = await resp.json();
                console.log('✅ InfluxDB:', data.status);
            } catch (e) {
                console.error('❌ InfluxDB 連線失敗:', e.message);
            }
        }
    };

    console.log('🌀 Wind Scraper v7.0 Ready!');
    console.log(`📦 ${DEVICES.length} 機組 × ${TAGS.length} 標籤`);
    console.log('ws.test() | ws.start() | ws.stop() | ws.status() | ws.reset()');
})();
