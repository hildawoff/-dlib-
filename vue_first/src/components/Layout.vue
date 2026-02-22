<template>
  <div class="page-wrapper">

    <!--顶部深蓝色背景-->
    <div class="header-block">
      <div class="top-bar-inner">
        <nav class="top-nav">
          <a href="#">About</a>
          <a href="#">Blog</a>
          <a href="#">Contact</a>
          <a href="#">Resources</a>
          <a href="#">FAQ</a>
        </nav>
      </div>
    </div>

    <!-- 深蓝色缎带和圆环 -->
    <div class="ribbon-zone">

      <!-- 圆形Logo -->
      <div class="logo-circle-wrap">
        <div class="logo-circle">
          <svg class="camera-svg" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
            <rect x="9" y="27" width="62" height="40" rx="6"
                  fill="none" stroke="#4a6070" stroke-width="3.2"/>
            <path d="M26 27 L26 20 Q26 16 30 16 L50 16 Q54 16 54 20 L54 27"
                  fill="none" stroke="#4a6070" stroke-width="3" stroke-linejoin="round"/>
            <circle cx="40" cy="47" r="13.5" fill="none" stroke="#4a6070" stroke-width="2.8"/>
            <circle cx="40" cy="47" r="8.5"  fill="none" stroke="#4a6070" stroke-width="2"/>
            <circle cx="40" cy="47" r="3.2"  fill="#4a6070"/>
            <circle cx="19" cy="36" r="3"    fill="none" stroke="#4a6070" stroke-width="2"/>
          </svg>
        </div>
      </div>

      <!-- 缎带栏本身 -->
      <div class="ribbon-bar">
        <!-- stitch lines -->
        <div class="stitch stitch-top"></div>
        <div class="stitch stitch-bottom"></div>

        <!-- 左侧导航栏 -->
        <div class="nav-left">
          <router-link to="/" class="nav-item active">Homepage</router-link>
          <router-link to="/register" class="nav-item">人脸登记</router-link>
          <router-link to="/recognize" class="nav-item">人脸识别</router-link>
        </div>

        <!-- 圆形中心间隔件 -->
        <div class="nav-center-gap"></div>

        <!-- 右侧导航栏 -->
        <div class="nav-right">
          <router-link to="/camera" class="nav-item">摄像头识别</router-link>
          <router-link to="/logs" class="nav-item">识别记录</router-link>
          <router-link to="/register" class="nav-item login-btn">
            登录&nbsp;/&nbsp;注册 <span class="caret">▾</span>
          </router-link>
        </div>
      </div>

      <!-- Wavy edge below ribbon (cream color, cuts into blue bg above) -->
      <div class="wavy-bottom">
        <svg xmlns="http://www.w3.org/2000/svg"
             viewBox="0 0 1440 36" preserveAspectRatio="none"
             width="100%" height="36px">
          <!-- The wave is cream-colored, sitting on the blue bg above -->
          <path
            d="M0,36
               C120,10 240,0  360,14
               C480,28 600,36 720,26
               C840,16 960,4  1080,12
               C1200,20 1320,32 1440,20
               L1440,36 Z"
            fill="#e8e4da"
          />
        </svg>
      </div>

    </div><!-- /ribbon-zone -->

    <!-- ═══════════════════════════════
         MAIN CONTENT (cream bg)
    ═══════════════════════════════ -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- ═══════════════════════════════
         FOOTER
    ═══════════════════════════════ -->
    <footer class="site-footer">
      <div class="footer-inner">
        <div class="footer-logo-wrap">
          <div class="footer-circle">
            <svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
              <circle cx="30" cy="30" r="26" fill="none" stroke="#7a8a9a" stroke-width="2"/>
              <rect x="13" y="21" width="34" height="24" rx="3" fill="none" stroke="#7a8a9a" stroke-width="1.8"/>
              <path d="M21 21 L21 17 Q21 14 24 14 L36 14 Q39 14 39 17 L39 21"
                    fill="none" stroke="#7a8a9a" stroke-width="1.8" stroke-linejoin="round"/>
              <circle cx="30" cy="33" r="7"   fill="none" stroke="#7a8a9a" stroke-width="1.5"/>
              <circle cx="30" cy="33" r="3.5" fill="#7a8a9a"/>
              <circle cx="19" cy="27" r="1.8" fill="none" stroke="#7a8a9a" stroke-width="1.2"/>
            </svg>
          </div>
          <div>
            <div class="footer-brand">FaceID</div>
            <div class="footer-slogan">slogan will be here</div>
          </div>
        </div>
        <div class="footer-copy">All rights reserved &copy; {{ currentYear }}</div>
        <div class="footer-credit">Powered by Vue3</div>
      </div>
    </footer>

  </div>
</template>

<script setup>
// 返回年份
import { computed } from 'vue'
const currentYear = computed(() => new Date().getFullYear())
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;700&family=Noto+Sans+SC:wght@300;400&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.page-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: 'Noto Sans SC', sans-serif;
}

/* ═══════════════════════════════════════
   BLUE HEADER — top half above the ribbon
═══════════════════════════════════════ */
.header-block {
  background-color: #2b4155;
  background-image:
    repeating-linear-gradient(
      -45deg,
      rgba(255,255,255,0.028) 0px,
      rgba(255,255,255,0.028) 1px,
      transparent 1px,
      transparent 7px
    ),
    radial-gradient(ellipse at 50% 0%, #3d5e74 0%, #1e3245 100%);
  /* exact height = top-bar + half the ribbon height (26px) + circle protrusion (28px) */
  padding-bottom: 0;
}

.top-bar-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 10px 28px 28px;   /* generous bottom pad so circle area has space */
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.top-nav { display: flex; gap: 14px; }
.top-nav a {
  color: #9ab4c4;
  text-decoration: none;
  transition: color .15s;
}
.top-nav a:hover { color: #fff; }

/* ═══════════════════════════════════════
   RIBBON ZONE
   This wrapper has NO background so the
   blue header shows through above it, and
   cream shows through below.
   The ribbon-bar is absolutely positioned
   to span vertically over both halves.
═══════════════════════════════════════ */
.ribbon-zone {
  position: relative;
  /* Total height = ribbon (52px) + half-circle protrusion above (30px) + wave (36px) */
  height: 118px;
  /* The top half of this zone sits over blue header, so we pull it up */
  margin-top: -30px;    /* pull up so circle starts in the blue area */
  z-index: 10;
  background: transparent;
}

/* ── Circle logo ── */
.logo-circle-wrap {
  position: absolute;
  left: 50%;
  top: 0;               /* circle top starts at the top of ribbon-zone (in blue) */
  transform: translateX(-50%);
  z-index: 30;
}

.logo-circle {
  width: 112px;
  height: 112px;
  border-radius: 50%;
  background: radial-gradient(circle at 38% 35%, #f2efe8 0%, #dbd8d0 55%, #cac7be 100%);
  border: 4px solid #18293a;
  box-shadow:
    0 0 0 3px rgba(255,255,255,0.6),
    0 0 0 6px #18293a,
    0 8px 30px rgba(0,0,0,0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform .25s ease;
}
.logo-circle:hover { transform: scale(1.05); }
.camera-svg { width: 64px; height: 64px; }

/* ── Ribbon bar ── */
.ribbon-bar {
  position: absolute;
  left: 0; right: 0;
  /* vertically centred: circle is 112px, ribbon is 52px → top = (112-52)/2 = 30px */
  top: 30px;
  height: 52px;
  background: linear-gradient(180deg, #253544 0%, #1c2c3a 48%, #253544 100%);
  border-top:    1px solid rgba(255,255,255,0.12);
  border-bottom: 1px solid rgba(0,0,0,0.45);
  display: flex;
  align-items: center;
  z-index: 20;
}

/* Stitch lines */
.stitch {
  position: absolute;
  left: 0; right: 0;
  height: 0;
  border-top: 1.5px dashed rgba(255,255,255,0.16);
  pointer-events: none;
  z-index: 25;
}
.stitch-top    { top: 6px; }
.stitch-bottom { bottom: 6px; }

/* Nav groups */
.nav-left, .nav-right {
  display: flex;
  align-items: center;
  height: 100%;
  flex: 1;
}
.nav-right { justify-content: flex-end; }

/* Centre gap so items don't go under the circle (112px wide) */
.nav-center-gap { width: 128px; flex-shrink: 0; }

.nav-item {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 18px;
  color: #8ab0c4;
  text-decoration: none;
  font-family: 'Oswald', sans-serif;
  font-size: 12.5px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  white-space: nowrap;
  transition: color .15s, background .15s;
  position: relative;
}
.nav-item:hover,
.nav-item.active { color: #deedf8; background: rgba(255,255,255,0.05); }

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0; left: 10px; right: 10px;
  height: 2.5px;
  background: #5a9ab8;
  border-radius: 2px 2px 0 0;
}

.nav-item.login-btn { color: #c8a030; }
.nav-item.login-btn:hover { color: #e6c040; }
.caret { font-size: 10px; margin-left: 3px; opacity: .75; }

/* ── Wavy bottom of ribbon-zone ── */
.wavy-bottom {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  line-height: 0;
  font-size: 0;
  z-index: 15;   /* above ribbon bar bottom edge */
}
.wavy-bottom svg { display: block; }

/* ═══════════════════════════════════════
   MAIN CONTENT — cream/parchment
═══════════════════════════════════════ */
.main-content {
  flex: 1;
  background-color: #e8e4da;
  background-image:
    radial-gradient(ellipse at 18% 60%, rgba(200,195,178,0.22) 0%, transparent 52%),
    radial-gradient(ellipse at 82% 18%, rgba(200,195,178,0.15) 0%, transparent 52%);
  padding: 48px 24px 40px;
}

/* ═══════════════════════════════════════
   FOOTER
═══════════════════════════════════════ */
.site-footer {
  background: linear-gradient(180deg, #d4d1c7 0%, #c7c4b9 100%);
  border-top: 1px solid #afaca1;
}
.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.footer-logo-wrap { display: flex; align-items: center; gap: 10px; }
.footer-circle {
  width: 58px; height: 58px;
  border-radius: 50%;
  background: radial-gradient(circle at 38% 36%, #eae7de 0%, #d0cdc4 100%);
  border: 2px solid #8a9aaa;
  box-shadow: inset 0 0 0 2px rgba(255,255,255,.28), 0 2px 8px rgba(0,0,0,.18);
  display: flex; align-items: center; justify-content: center;
  padding: 8px;
}
.footer-brand  { font-family:'Oswald',sans-serif; font-size:17px; font-weight:600; color:#44586a; letter-spacing:.04em; line-height:1.1; }
.footer-slogan { font-size:9px; color:#8a9aaa; letter-spacing:.05em; font-style:italic; }
.footer-copy   { font-size:11px; color:#7a8a98; }
.footer-credit { font-size:11px; color:#7a8a98; }
</style>