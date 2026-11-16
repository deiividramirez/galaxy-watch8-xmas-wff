/**
 * Galaxy Watch 8 Holiday Watch Face — Interactive WFF v4 Simulator
 * Strictly mirrors Watch Face Format 450x450 virtual coordinate space,
 * [DAY_OF_YEAR] Christmas countdown logic, <= 15 FPS snow/lights cap,
 * PhotosConfiguration custom photo support, and all 5 Samsung complications.
 */
(function () {
  "use strict";

  const state = {
    powerMode: "active", // "active" | "aod"
    ecoMode: "auto_eco", // "auto_eco" | "max_battery" | "vivid_always"
    wakeBurstStartTs: performance.now(),
    model: "44mm",       // "44mm" (480px) | "40mm" (438px) | "classic" (438px + bezel)
    clockMode: "digital", // "digital" (default unobstructed) | "analog" | "hybrid"
    theme: "cranberry",  // "cranberry" | "frost" | "evergreen"
    portrait: "primary", // "primary" | "alt" | "custom_photo"
    customPhotoDataUrl: null,
    lockInfoVisible: true, // WFF BooleanConfiguration id="lock_info_visible"
    watchLocked: false,    // Simulated Watch 8 PIN-lock state
    snowEnabled: true,
    inspectorEnabled: false,
    liveClock: true,
    simDate: new Date(),
    manualMinutes: 8 * 60 + 52,
    weatherTemp: 19,
    weatherCond: "sunny",
    uvIndex: 4,
    heartRate: 83,
    battery: 83,
    energyScore: 86,
    gyroX: 0,
    gyroY: 0,
  };

  // DOM References
  const watchChassis = document.getElementById("watchChassis");
  const wffScene = document.getElementById("wffScene");
  const wffBgLayer = document.getElementById("wffBgLayer");
  const wffSkyOverlay = document.getElementById("wffSkyOverlay");
  const centerpieceMedallion = document.getElementById("centerpieceMedallion");
  const centerpieceActiveImg = document.getElementById("centerpieceActiveImg");
  const centerpieceAodImg = document.getElementById("centerpieceAodImg");

  const dialTicksGroup = document.getElementById("dialTicksGroup");
  const fairyLightsGroup = document.getElementById("fairyLightsGroup");
  const energyArcTrack = document.getElementById("energyArcTrack");
  const energyArcFill = document.getElementById("energyArcFill");
  const bezelSecondOrnament = document.getElementById("bezelSecondOrnament");

  const xmasIcon = document.getElementById("xmasIcon");
  const xmasCountdownText = document.getElementById("xmasCountdownText");
  const digitalHhmm = document.getElementById("digitalHhmm");
  const digitalSec = document.getElementById("digitalSec");
  const digitalDate = document.getElementById("digitalDate");
  const analogDatePill = document.getElementById("analogDatePill");

  const hourHandGroup = document.getElementById("hourHandGroup");
  const minuteHandGroup = document.getElementById("minuteHandGroup");
  const secondHandGroup = document.getElementById("secondHandGroup");

  const weatherIconImg = document.getElementById("weatherIconImg");
  const weatherTemp = document.getElementById("weatherTemp");
  const uvValueText = document.getElementById("uvValueText");
  const uvBarFill = document.getElementById("uvBarFill");
  const hrValueText = document.getElementById("hrValueText");
  const hrBarFill = document.getElementById("hrBarFill");
  const heartIcon = document.getElementById("heartIcon");
  const battValueText = document.getElementById("battValueText");
  const battBarFill = document.getElementById("battBarFill");
  const energyValueText = document.getElementById("energyValueText");

  const snowCanvas = document.getElementById("snowCanvas");
  const snowCtx = snowCanvas.getContext("2d");
  const wffInspectorOverlay = document.getElementById("wffInspectorOverlay");

  const telScreenSpec = document.getElementById("telScreenSpec");
  const telScaleSpec = document.getElementById("telScaleSpec");
  const telOprValue = document.getElementById("telOprValue");
  const telRamValue = document.getElementById("telRamValue");

  const SVG_NS = "http://www.w3.org/2000/svg";

  // 1. Build 60 Minute Ticks + 12 Twinkling Holiday Fairy Bulbs on 450x450 SVG
  const fairyBulbs = [];
  const bulbPalette = ["#ff5252", "#ffd740", "#69f0ae", "#40c4ff"];

  function initDialSvg() {
    for (let i = 0; i < 60; i++) {
      const deg = i * 6;
      const rad = ((deg - 90) * Math.PI) / 180;
      const isHour = i % 5 === 0;
      const rOuter = 220;
      const rInner = isHour ? 210 : 215;

      const line = document.createElementNS(SVG_NS, "line");
      line.setAttribute("x1", (225 + rOuter * Math.cos(rad)).toFixed(2));
      line.setAttribute("y1", (225 + rOuter * Math.sin(rad)).toFixed(2));
      line.setAttribute("x2", (225 + rInner * Math.cos(rad)).toFixed(2));
      line.setAttribute("y2", (225 + rInner * Math.sin(rad)).toFixed(2));
      line.setAttribute("stroke", isHour ? "rgba(245,197,66,0.75)" : "rgba(255,255,255,0.22)");
      line.setAttribute("stroke-width", isHour ? "2.6" : "1");
      line.setAttribute("stroke-linecap", "round");
      dialTicksGroup.appendChild(line);

      if (isHour) {
        const hourIndex = i / 5;
        const bx = 225 + 204 * Math.cos(rad);
        const by = 225 + 204 * Math.sin(rad);
        const bulb = document.createElementNS(SVG_NS, "circle");
        bulb.setAttribute("cx", bx.toFixed(2));
        bulb.setAttribute("cy", by.toFixed(2));
        bulb.setAttribute("r", "3.2");
        bulb.setAttribute("fill", bulbPalette[hourIndex % bulbPalette.length]);
        bulb.setAttribute("filter", "url(#softGlow)");
        fairyLightsGroup.appendChild(bulb);
        fairyBulbs.push(bulb);
      }
    }
  }

  // Helper: Polar SVG Arc Path (Angles in degrees, 0 deg = 12 o'clock clockwise)
  function describeArc(cx, cy, radius, startDeg, endDeg) {
    const startRad = ((startDeg - 90) * Math.PI) / 180;
    const endRad = ((endDeg - 90) * Math.PI) / 180;
    const x1 = cx + radius * Math.cos(startRad);
    const y1 = cy + radius * Math.sin(startRad);
    const x2 = cx + radius * Math.cos(endRad);
    const y2 = cy + radius * Math.sin(endRad);
    const largeArc = Math.abs(endDeg - startDeg) <= 180 ? "0" : "1";
    const sweep = endDeg >= startDeg ? "1" : "0";
    return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${radius} ${radius} 0 ${largeArc} ${sweep} ${x2.toFixed(2)} ${y2.toFixed(2)}`;
  }

  // 2. Exact Watch Face Format [DAY_OF_YEAR] & Leap Year Christmas Countdown
  function isLeapYear(year) {
    return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
  }

  function getDayOfYear(date) {
    const start = new Date(date.getFullYear(), 0, 0);
    const diff = date - start + (start.getTimezoneOffset() - date.getTimezoneOffset()) * 60 * 1000;
    return Math.floor(diff / 86400000);
  }

  function updateXmasCountdown(date) {
    const year = date.getFullYear();
    const doy = getDayOfYear(date);
    const xmasDoy = isLeapYear(year) ? 360 : 359;
    const daysInYear = isLeapYear(year) ? 366 : 365;

    if (doy === xmasDoy) {
      xmasIcon.textContent = "🎅";
      xmasCountdownText.textContent = "MERRY XMAS!";
    } else if (doy === xmasDoy - 1) {
      xmasIcon.textContent = "✨";
      xmasCountdownText.textContent = "XMAS EVE!";
    } else if (doy < xmasDoy) {
      const rem = xmasDoy - doy;
      xmasIcon.textContent = "🎄";
      xmasCountdownText.textContent = `${rem}D TO XMAS`;
    } else {
      const nextYearXmas = isLeapYear(year + 1) ? 360 : 359;
      const rem = daysInYear - doy + nextYearXmas;
      xmasIcon.textContent = "🎄";
      xmasCountdownText.textContent = `${rem}D TO XMAS`;
    }
  }

  // 3. Render Clock (Digital, Analog, Hybrid)
  const DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

  function updateClockDisplay() {
    let now;
    if (state.liveClock) {
      now = new Date();
      // Keep date preset day/month if user clicked Dec 24 or Dec 25 while live seconds tick
      now.setFullYear(state.simDate.getFullYear(), state.simDate.getMonth(), state.simDate.getDate());
    } else {
      now = new Date(state.simDate.getTime());
      const hh = Math.floor(state.manualMinutes / 60);
      const mm = state.manualMinutes % 60;
      now.setHours(hh, mm, 27, 0);
    }

    const hours = now.getHours();
    const minutes = now.getMinutes();
    const seconds = now.getSeconds();
    const millis = state.liveClock ? now.getMilliseconds() : 0;

    const pad = (n) => String(n).padStart(2, "0");
    digitalHhmm.textContent = `${pad(hours)}:${pad(minutes)}`;
    digitalSec.textContent = pad(seconds);

    const dateStr = `${DAYS[now.getDay()]} · ${MONTHS[now.getMonth()]} ${now.getDate()}`;
    digitalDate.textContent = dateStr;
    analogDatePill.textContent = dateStr;

    updateXmasCountdown(now);

    // Smooth WFF Analog Hand Angles around (225, 225) — Battery-Saver Aware!
    const lowBatteryFreeze = state.battery <= 25;
    const hideSweep = state.powerMode === "aod" || state.ecoMode === "max_battery" || lowBatteryFreeze;
    const quantMillis = state.ecoMode === "auto_eco" ? Math.floor(millis / 200) * 200 : millis;
    const smoothSec = seconds + (state.liveClock ? quantMillis / 1000 : 0);
    const secDeg = smoothSec * 6;
    const minDeg = (minutes + smoothSec / 60) * 6;
    const hourDeg = ((hours % 12) + minutes / 60) * 30;

    hourHandGroup.setAttribute("transform", `rotate(${hourDeg.toFixed(2)} 225 225)`);
    minuteHandGroup.setAttribute("transform", `rotate(${minDeg.toFixed(2)} 225 225)`);
    secondHandGroup.style.display = hideSweep ? "none" : "";
    bezelSecondOrnament.style.display = hideSweep ? "none" : "";
    if (!hideSweep) {
      secondHandGroup.setAttribute("transform", `rotate(${secDeg.toFixed(2)} 225 225)`);
      bezelSecondOrnament.setAttribute("transform", `rotate(${secDeg.toFixed(2)} 225 225)`);
    }
  }

  // 4. Render All 5 High-Visibility Samsung Complications + Live Weather Sky
  function updateComplications() {
    const condMap = {
      sunny:       { icon: "assets/icons/wx_sunny.webp",       sky: "assets/icons/sky_sunny.webp",         showSky: true },
      partly_day:  { icon: "assets/icons/wx_partly_day.webp",  sky: "assets/icons/sky_partly_cloudy.webp", showSky: true },
      windy:       { icon: "assets/icons/wx_windy.webp",       sky: "assets/icons/sky_cloudy_mist.webp",   showSky: true },
      rain:        { icon: "assets/icons/wx_rain.webp",        sky: "assets/icons/sky_rain_storm.webp",    showSky: true },
      storm:       { icon: "assets/icons/wx_storm.webp",       sky: "assets/icons/sky_rain_storm.webp",    showSky: true },
      snow:        { icon: "assets/icons/wx_snow.webp",        sky: "assets/icons/sky_cloudy_mist.webp",   showSky: false },
      clear_night: { icon: "assets/icons/wx_clear_night.webp", sky: "assets/icons/sky_starry_night.webp",  showSky: true },
      fog:         { icon: "assets/icons/wx_fog.webp",         sky: "assets/icons/sky_cloudy_mist.webp",   showSky: true },
    };
    const w = condMap[state.weatherCond] || condMap.sunny;
    if (weatherIconImg) weatherIconImg.src = state.watchLocked ? "assets/icons/wx_partly_day.webp" : w.icon;
    if (wffSkyOverlay) {
      wffSkyOverlay.src = w.sky;
      wffSkyOverlay.style.opacity = (state.powerMode === "aod" || state.watchLocked) ? "0" : (w.showSky ? "0.95" : "0");
    }

    const privateLocked = state.watchLocked && !state.lockInfoVisible;

    // Slot 1: Live Weather
    weatherTemp.style.display = privateLocked ? "none" : "";
    weatherTemp.textContent = state.watchLocked ? "--°" : `${state.weatherTemp}°`;

    // Slot 2: Sun Heat / UV Index (0..11)
    uvValueText.style.display = privateLocked ? "none" : "";
    uvBarFill.parentElement.style.display = privateLocked ? "none" : "";
    uvValueText.textContent = state.watchLocked ? "UV --" : `UV ${state.uvIndex}`;
    uvBarFill.style.width = state.watchLocked ? "0%" : `${Math.max(12, Math.min(100, (state.uvIndex / 11) * 100)).toFixed(0)}%`;

    // Slot 3: Samsung Health Heart Rate
    hrValueText.style.display = privateLocked ? "none" : "";
    hrBarFill.parentElement.style.display = privateLocked ? "none" : "";
    hrValueText.textContent = state.watchLocked ? "--" : String(state.heartRate);
    const hrPct = Math.max(14, Math.min(100, ((state.heartRate - 45) / (185 - 45)) * 100));
    hrBarFill.style.width = state.watchLocked ? "0%" : `${hrPct.toFixed(0)}%`;
    heartIcon.style.animationDuration = `${(60 / Math.max(50, state.heartRate)).toFixed(2)}s`;

    // Slot 4: Watch Battery ([BATTERY_PERCENT] stays 100% live even when watch is locked if lockInfoVisible == TRUE!)
    battValueText.style.display = privateLocked ? "none" : "";
    battBarFill.parentElement.style.display = privateLocked ? "none" : "";
    battValueText.textContent = `${state.battery}%`;
    battValueText.style.color = state.battery <= 25 ? "#ff6e40" : "#69f0ae";
    battBarFill.style.width = `${Math.max(12, state.battery)}%`;
    battBarFill.style.background = state.battery <= 25 ? "#ff6e40" : "#69f0ae";
    heartIcon.style.animationPlayState = (state.ecoMode === "max_battery" || state.battery <= 25 || state.watchLocked) ? "paused" : "running";

    // Slot 5: Samsung Health Energy Score (Unclipped Bottom Curved Arc r=186, 155..205 deg)
    const arcRadius = 186;
    const startAngle = 205;
    const totalSpan = 50;
    energyArcTrack.setAttribute("d", describeArc(225, 225, arcRadius, 155, 205));

    energyValueText.style.display = privateLocked ? "none" : "";
    energyArcFill.style.display = (privateLocked || state.watchLocked) ? "none" : "";
    const filledSpan = Math.max(0.06, state.energyScore / 100) * totalSpan;
    const fillStart = startAngle - filledSpan;
    energyArcFill.setAttribute("d", describeArc(225, 225, arcRadius, fillStart, startAngle));
    energyValueText.textContent = state.watchLocked ? "--" : String(state.energyScore);
  }

  // 5. Wrist-Tilt Snowglobe Parallax ([ACCELEROMETER_ANGLE_X] / [ACCELEROMETER_ANGLE_Y])
  function applyGyroParallax() {
    if (state.powerMode === "aod" || !state.snowEnabled) {
      centerpieceMedallion.style.transform = "translate3d(0, 0, 0)";
      wffBgLayer.style.transform = "translate3d(0, 0, 0)";
      return;
    }
    const shiftX = (state.gyroX / 15) * 6;
    const shiftY = (state.gyroY / 15) * 6;
    centerpieceMedallion.style.transform = `translate3d(${shiftX.toFixed(1)}px, ${shiftY.toFixed(1)}px, 0)`;
    wffBgLayer.style.transform = `translate3d(${(-shiftX * 1.4).toFixed(1)}px, ${(-shiftY * 1.4).toFixed(1)}px, 0)`;
  }

  // 6. <= 15 FPS Falling Snow + Fairy Light Twinkle Loop (WFF AnimatedImages Compliance)
  const snowflakes = Array.from({ length: 42 }, () => ({
    x: Math.random() * 450,
    y: Math.random() * 450,
    r: 1.2 + Math.random() * 2.4,
    vy: 1.4 + Math.random() * 2.2,
    drift: (Math.random() - 0.5) * 0.9,
    alpha: 0.35 + Math.random() * 0.55,
  }));

  let lastFrameTime = 0;
  let tickCount = 0;

  function animationLoop(ts) {
    requestAnimationFrame(animationLoop);

    // Update smooth clock hands
    updateClockDisplay();

    // Enforce strict WFF <= 15 FPS (~66.7ms interval) for snow & twinkling lights
    if (ts - lastFrameTime < 67) return;
    lastFrameTime = ts;
    tickCount++;

    // Smart Battery Saver Gate: Pause all particles & twinkle if Battery <= 25%, Max Battery, or post-4s Auto Eco burst!
    const lowBattCutoff = state.battery <= 25;
    const burstExpired = state.ecoMode === "auto_eco" && (ts - state.wakeBurstStartTs > 4200);
    const freezeParticles = state.powerMode !== "active" || state.ecoMode === "max_battery" || lowBattCutoff;

    if (state.powerMode === "active") {
      if (freezeParticles || burstExpired) {
        for (let i = 0; i < fairyBulbs.length; i++) {
          fairyBulbs[i].setAttribute("opacity", i % 2 === 0 ? "0.92" : "0.45");
        }
      } else {
        for (let i = 0; i < fairyBulbs.length; i++) {
          const wave = 0.45 + 0.55 * Math.sin(tickCount * 0.32 + i * 1.1);
          fairyBulbs[i].setAttribute("opacity", wave.toFixed(2));
        }
      }
    }

    snowCtx.clearRect(0, 0, 450, 450);
    if (freezeParticles) return;

    const stepMotion = !burstExpired;

    const windTilt = (state.gyroX / 15) * 1.8;

    if (state.weatherCond === "windy") {
      snowCtx.lineCap = "round";
      snowCtx.lineWidth = 2.2;
      for (let i = 0; i < 16; i++) {
        const f = snowflakes[i];
        if (stepMotion) f.x = (f.x + 12 + f.vy * 2.5) % 450;
        const wy = f.y + Math.sin(tickCount * 0.28 + i) * 5;
        snowCtx.strokeStyle = `rgba(179, 229, 252, ${(f.alpha * 0.72).toFixed(2)})`;
        snowCtx.beginPath();
        snowCtx.moveTo(f.x, wy);
        snowCtx.quadraticCurveTo(f.x + 24, wy - 4, f.x + 48, wy);
        snowCtx.stroke();
      }
      return;
    }

    if (state.weatherCond === "rain" || state.weatherCond === "storm") {
      snowCtx.lineCap = "round";
      snowCtx.lineWidth = 2.1;
      for (let i = 0; i < 32; i++) {
        const f = snowflakes[i];
        if (stepMotion) {
          f.y = (f.y + 11 + f.vy * 2.8) % 450;
          f.x = (f.x - 2.6 + windTilt + 450) % 450;
        }
        snowCtx.strokeStyle = `rgba(100, 196, 255, ${(f.alpha * 0.85).toFixed(2)})`;
        snowCtx.beginPath();
        snowCtx.moveTo(f.x, f.y);
        snowCtx.lineTo(f.x - 4, f.y + 15);
        snowCtx.stroke();
      }
      return;
    }

    if (!state.snowEnabled && state.weatherCond !== "snow") return;

    const weatherBoost = state.weatherCond === "snow" ? 1.45 : 0.85;
    const count = state.weatherCond === "snow" ? snowflakes.length : 24;

    for (let i = 0; i < count; i++) {
      const f = snowflakes[i];
      if (stepMotion) {
        f.y += f.vy * weatherBoost;
        f.x += f.drift + windTilt;
        if (f.y > 450) {
          f.y = -4;
          f.x = Math.random() * 450;
        }
        if (f.x > 450) f.x = 0;
        if (f.x < 0) f.x = 450;
      }

      snowCtx.beginPath();
      snowCtx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
      snowCtx.fillStyle = `rgba(255, 255, 255, ${f.alpha.toFixed(2)})`;
      snowCtx.fill();
    }
  }

  // 7. Responsive Watch Rig Viewport Scaling (Zero X/Y Overflow on Desktop & Phones)
  const watchRigViewport = document.getElementById("watchRigViewport");
  const watchRig = document.getElementById("watchRig");
  const stageHeader = document.getElementById("stageHeader");
  const telemetryBar = document.getElementById("telemetryBar");

  function fitWatchRigToViewport() {
    if (!watchRigViewport || !watchRig) return;

    // Exact symmetric pixel footprint of Watch 8 chassis + side buttons + straps
    let naturalW = 558;
    let naturalH = 604;
    if (state.model === "40mm") {
      naturalW = 516;
      naturalH = 562;
    } else if (state.model === "classic") {
      naturalW = 536;
      naturalH = 582;
    }

    const vw = document.documentElement.clientWidth || window.innerWidth;
    const vh = window.innerHeight;
    const isDesktop = vw > 1024 && vh >= 560;

    let scale = 1;
    if (isDesktop) {
      const stageEl = watchRigViewport.parentElement;
      const stageW = stageEl ? stageEl.clientWidth : vw - 460;
      const headerH = stageHeader ? stageHeader.offsetHeight : 82;
      const telH = telemetryBar ? telemetryBar.offsetHeight : 52;
      const availW = Math.max(260, stageW - 20);
      const availH = Math.max(250, vh - headerH - telH - 72);
      scale = Math.min(1, availW / naturalW, availH / naturalH);
    } else if (vw > vh) {
      // Landscape phone / tablet: fit both width and landscape height cleanly
      const availW = Math.max(240, vw - 32);
      const availH = Math.max(240, vh - 40);
      scale = Math.min(0.92, availW / naturalW, availH / naturalH);
    } else {
      // Portrait phone / tablet: depend purely on width to prevent scroll-bar URL-bar jitter
      const availW = Math.max(240, vw - 28);
      const maxPortraitScale = vw <= 600 ? 0.82 : 0.95;
      scale = Math.min(maxPortraitScale, availW / naturalW);
    }

    scale = Math.max(0.42, scale);
    watchRig.style.width = `${naturalW}px`;
    watchRig.style.transform = `scale(${scale.toFixed(4)})`;
    watchRigViewport.style.width = `${Math.round(naturalW * scale)}px`;
    watchRigViewport.style.height = `${Math.round(naturalH * scale)}px`;
  }

  // Update Hardware Model, Theme, Mode & WFF Optimizer Telemetry
  function syncSceneClassesAndTelemetry() {
    watchChassis.className = `watch8-cushion model-${state.model}`;
    wffScene.className = `wff-scene theme-${state.theme} clock-${state.clockMode} mode-${state.powerMode}`;
    wffInspectorOverlay.hidden = !state.inspectorEnabled;

    if (state.model === "44mm") {
      telScreenSpec.textContent = "44mm · 480×480 px (1.47\")";
      telScaleSpec.textContent = "1.067× (from 450px)";
    } else if (state.model === "40mm") {
      telScreenSpec.textContent = "40mm · 438×438 px (1.34\")";
      telScaleSpec.textContent = "0.973× (from 450px)";
    } else {
      telScreenSpec.textContent = "46mm Classic · 438×438 px";
      telScaleSpec.textContent = "0.973× + Rotating Bezel";
    }

    const aodOpr = state.clockMode === "analog" ? 3.5 : 3.95;
    telOprValue.textContent = `${aodOpr.toFixed(2)}% (< 15% OK)`;

    if (state.powerMode === "aod") {
      telRamValue.textContent = "6.10 MB / 10 MB AOD OK";
    } else {
      telRamValue.textContent = "8.98 MB / 100 MB Active OK";
    }

    const telFpsValue = document.getElementById("telFpsValue");
    if (telFpsValue) {
      if (state.powerMode === "aod" || state.ecoMode === "max_battery" || state.battery <= 25) {
        telFpsValue.textContent = "0 FPS (Eco Frozen)";
      } else if (state.ecoMode === "auto_eco") {
        telFpsValue.textContent = "4s Burst -> 5Hz Eco";
      } else {
        telFpsValue.textContent = "8-15 FPS Vivid";
      }
    }

    applyGyroParallax();
    requestAnimationFrame(fitWatchRigToViewport);
  }

  // 8. Wire Interactive Controls
  function bindControls() {
    // Segmented buttons
    document.querySelectorAll("[data-power]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.powerMode = btn.dataset.power;
        if (state.powerMode === "active") state.wakeBurstStartTs = performance.now();
        document.querySelectorAll("[data-power]").forEach((b) => b.classList.toggle("active", b === btn));
        syncSceneClassesAndTelemetry();
      });
    });

    document.querySelectorAll("[data-eco]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.ecoMode = btn.dataset.eco;
        state.wakeBurstStartTs = performance.now();
        document.querySelectorAll("[data-eco]").forEach((b) => b.classList.toggle("active", b === btn));
        updateComplications();
        syncSceneClassesAndTelemetry();
      });
    });

    document.querySelectorAll("[data-model]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.model = btn.dataset.model;
        document.querySelectorAll("[data-model]").forEach((b) => b.classList.toggle("active", b === btn));
        syncSceneClassesAndTelemetry();
      });
    });

    document.querySelectorAll("[data-clock]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.clockMode = btn.dataset.clock;
        document.querySelectorAll("[data-clock]").forEach((b) => b.classList.toggle("active", b === btn));
        syncSceneClassesAndTelemetry();
      });
    });

    document.querySelectorAll("[data-theme]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.theme = btn.dataset.theme;
        document.querySelectorAll("[data-theme]").forEach((b) => b.classList.toggle("active", b === btn));
        syncSceneClassesAndTelemetry();
      });
    });

    document.querySelectorAll("[data-portrait]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const chosen = btn.dataset.portrait;
        if (chosen === "custom_photo" && !state.customPhotoDataUrl) {
          document.getElementById("customPhotoInput").click();
          return;
        }
        state.portrait = chosen;
        document.querySelectorAll("[data-portrait]").forEach((b) => b.classList.toggle("active", b === btn));
        if (state.portrait === "primary") {
          centerpieceActiveImg.src = "assets/centerpiece_primary.png";
          centerpieceAodImg.src = "assets/centerpiece_aod.png";
        } else if (state.portrait === "alt") {
          centerpieceActiveImg.src = "assets/centerpiece_alt.png";
          centerpieceAodImg.src = "assets/centerpiece_alt_aod.png";
        } else if (state.portrait === "custom_photo" && state.customPhotoDataUrl) {
          centerpieceActiveImg.src = state.customPhotoDataUrl;
          centerpieceAodImg.src = "assets/centerpiece_aod.png";
        }
      });
    });

    // Hardware side buttons on Watch 8 frame
    document.getElementById("hwBtnHome").addEventListener("click", () => {
      const next = state.powerMode === "active" ? "aod" : "active";
      document.querySelector(`[data-power="${next}"]`).click();
    });

    document.getElementById("hwBtnBack").addEventListener("click", () => {
      const order = ["digital", "analog", "hybrid"];
      const next = order[(order.indexOf(state.clockMode) + 1) % order.length];
      document.querySelector(`[data-clock="${next}"]`).click();
    });

    // Checkboxes
    const toggleLockInfoEl = document.getElementById("toggleLockInfo");
    if (toggleLockInfoEl) {
      toggleLockInfoEl.addEventListener("change", (e) => {
        state.lockInfoVisible = e.target.checked;
        updateComplications();
      });
    }

    const toggleWatchLockedEl = document.getElementById("toggleWatchLocked");
    if (toggleWatchLockedEl) {
      toggleWatchLockedEl.addEventListener("change", (e) => {
        state.watchLocked = e.target.checked;
        updateComplications();
      });
    }

    document.getElementById("toggleSnow").addEventListener("change", (e) => {
      state.snowEnabled = e.target.checked;
      syncSceneClassesAndTelemetry();
    });

    document.getElementById("toggleInspector").addEventListener("change", (e) => {
      state.inspectorEnabled = e.target.checked;
      syncSceneClassesAndTelemetry();
    });

    const liveClockChk = document.getElementById("toggleLiveClock");
    const timeScrubber = document.getElementById("timeScrubber");
    const timeScrubberOut = document.getElementById("timeScrubberOut");

    liveClockChk.addEventListener("change", (e) => {
      state.liveClock = e.target.checked;
    });

    timeScrubber.addEventListener("input", (e) => {
      state.liveClock = false;
      liveClockChk.checked = false;
      state.manualMinutes = Number(e.target.value);
      const hh = String(Math.floor(state.manualMinutes / 60)).padStart(2, "0");
      const mm = String(state.manualMinutes % 60).padStart(2, "0");
      timeScrubberOut.textContent = `${hh}:${mm}`;
      updateClockDisplay();
    });

    // Date Presets for Christmas Countdown verification
    document.querySelectorAll("[data-date-preset]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const preset = btn.dataset.datePreset;
        const yr = new Date().getFullYear();
        if (preset === "now") {
          state.simDate = new Date();
          state.liveClock = true;
          liveClockChk.checked = true;
        } else if (preset === "eve") {
          state.simDate = new Date(yr, 11, 24, 20, 30, 0);
        } else if (preset === "xmas") {
          state.simDate = new Date(yr, 11, 25, 9, 0, 0);
        } else if (preset === "tenTen") {
          state.liveClock = false;
          liveClockChk.checked = false;
          state.manualMinutes = 10 * 60 + 10;
          timeScrubber.value = String(state.manualMinutes);
          timeScrubberOut.textContent = "10:10";
        }
        updateClockDisplay();
      });
    });

    // 5 Samsung Complication Controls
    document.getElementById("weatherCondSelect").addEventListener("change", (e) => {
      state.weatherCond = e.target.value;
      updateComplications();
    });

    document.getElementById("weatherTempSlider").addEventListener("input", (e) => {
      state.weatherTemp = Number(e.target.value);
      document.getElementById("weatherTempOut").textContent = `${state.weatherTemp}°C`;
      updateComplications();
    });

    document.getElementById("uvSlider").addEventListener("input", (e) => {
      state.uvIndex = Number(e.target.value);
      document.getElementById("uvOut").textContent = `UV ${state.uvIndex}`;
      updateComplications();
    });

    document.getElementById("hrSlider").addEventListener("input", (e) => {
      state.heartRate = Number(e.target.value);
      document.getElementById("hrOut").textContent = `${state.heartRate} bpm`;
      updateComplications();
    });

    document.getElementById("battSlider").addEventListener("input", (e) => {
      state.battery = Number(e.target.value);
      document.getElementById("battOut").textContent = `${state.battery}%`;
      updateComplications();
      syncSceneClassesAndTelemetry();
    });

    document.getElementById("energySlider").addEventListener("input", (e) => {
      state.energyScore = Number(e.target.value);
      document.getElementById("energyOut").textContent = `${state.energyScore} / 100`;
      updateComplications();
    });

    // Hovering a complication control highlights the corresponding watch slot (and vice versa)
    document.querySelectorAll("[data-highlight-slot]").forEach((grp) => {
      const id = grp.dataset.highlightSlot;
      const slotEl = document.getElementById(`slot${id}`);
      grp.addEventListener("mouseenter", () => slotEl && slotEl.classList.add("slot-highlighted"));
      grp.addEventListener("mouseleave", () => slotEl && slotEl.classList.remove("slot-highlighted"));
    });

    document.querySelectorAll(".comp-slot").forEach((slotEl) => {
      slotEl.addEventListener("click", () => {
        state.inspectorEnabled = !state.inspectorEnabled;
        document.getElementById("toggleInspector").checked = state.inspectorEnabled;
        syncSceneClassesAndTelemetry();
      });
    });

    // Gyro sliders + Mouse move over Watch 8 screen
    const gyroXSlider = document.getElementById("gyroXSlider");
    const gyroYSlider = document.getElementById("gyroYSlider");
    const gyroXOut = document.getElementById("gyroXOut");
    const gyroYOut = document.getElementById("gyroYOut");

    gyroXSlider.addEventListener("input", (e) => {
      state.gyroX = Number(e.target.value);
      gyroXOut.textContent = `${state.gyroX}°`;
      applyGyroParallax();
    });

    gyroYSlider.addEventListener("input", (e) => {
      state.gyroY = Number(e.target.value);
      gyroYOut.textContent = `${state.gyroY}°`;
      applyGyroParallax();
    });

    const amoledViewport = document.getElementById("amoledViewport");
    function updateTiltFromPointer(clientX, clientY) {
      const rect = amoledViewport.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const nx = Math.max(-1, Math.min(1, ((clientX - rect.left) / rect.width) * 2 - 1));
      const ny = Math.max(-1, Math.min(1, ((clientY - rect.top) / rect.height) * 2 - 1));
      state.gyroX = Math.round(nx * 15);
      state.gyroY = Math.round(ny * 15);
      gyroXSlider.value = String(state.gyroX);
      gyroYSlider.value = String(state.gyroY);
      gyroXOut.textContent = `${state.gyroX}°`;
      gyroYOut.textContent = `${state.gyroY}°`;
      applyGyroParallax();
    }

    function resetTilt() {
      state.gyroX = 0;
      state.gyroY = 0;
      gyroXSlider.value = "0";
      gyroYSlider.value = "0";
      gyroXOut.textContent = "0°";
      gyroYOut.textContent = "0°";
      applyGyroParallax();
    }

    amoledViewport.addEventListener("mousemove", (e) => {
      updateTiltFromPointer(e.clientX, e.clientY);
    });
    amoledViewport.addEventListener("mouseleave", resetTilt);

    // Phone touch-tilt support across the watch screen
    amoledViewport.addEventListener(
      "touchmove",
      (e) => {
        if (e.touches && e.touches.length === 1) {
          updateTiltFromPointer(e.touches[0].clientX, e.touches[0].clientY);
        }
      },
      { passive: true }
    );
    amoledViewport.addEventListener("touchend", resetTilt, { passive: true });
    amoledViewport.addEventListener("touchcancel", resetTilt, { passive: true });

    window.addEventListener("resize", fitWatchRigToViewport);
    window.addEventListener("load", fitWatchRigToViewport);
    window.addEventListener("orientationchange", () => setTimeout(fitWatchRigToViewport, 120));

    // Auto-resolve APK download path when hosted at GitHub Pages site root vs local html/ folder
    const apkDownloadBtn = document.getElementById("apkDownloadBtn");
    if (
      apkDownloadBtn &&
      window.location.protocol.startsWith("http") &&
      !window.location.pathname.includes("/html/")
    ) {
      apkDownloadBtn.setAttribute("href", "./watch8-holiday-xmas.apk");
    }

    // Custom local photo live preview (FileReader DataURL — works over file://!)
    document.getElementById("customPhotoInput").addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        state.customPhotoDataUrl = ev.target.result;
        state.portrait = "custom_photo";
        centerpieceActiveImg.src = state.customPhotoDataUrl;
        document.querySelectorAll("[data-portrait]").forEach((b) =>
          b.classList.toggle("active", b.dataset.portrait === "custom_photo")
        );
      };
      reader.readAsDataURL(file);
    });
  }

  // Initialize Everything
  initDialSvg();
  bindControls();
  updateComplications();
  syncSceneClassesAndTelemetry();
  updateClockDisplay();
  requestAnimationFrame(animationLoop);
})();
