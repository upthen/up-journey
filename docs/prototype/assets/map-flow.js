/* up-journey v4 · 流程式地图体验
   第一幕：全屏地图（景点带年份）→ 点击景点 → 第二幕：地点故事面板 */
(function () {
  var BASE = (document.currentScript && document.currentScript.src)
    ? new URL('.', document.currentScript.src).href : '';

  var T = Object.assign({
    visited3: '#E8683A', visited2: '#F09A72', visited1: '#F7C7AF',
    none: '#EDE9E1', border: '#FAF8F4', cityDot: '#14586B', route: '#E8683A',
    label: '#3E4C57', legend: '#98A1AB', emphasis: '#F6E3D9'
  }, window.UJ_MAP_THEME || {});

  /* ---------- 数据（原型假数据，结构与 API 对齐） ---------- */
  var SPOTS = [
    { name: '滇池 · 海埂大坝', year: 2024, coord: [102.67, 24.98], city: '云南 · 昆明', photos: 21,
      blurb: '成千上万只红嘴鸥盘旋成一团灰白的云。哥哥举着饲料，海鸥落在手腕上啄食。',
      thumbs: ['gulls-boy.jpg', 'erhai-pano.jpg', 'erhai-village.jpg'], trip: '云南环线：从滇池到玉龙' },
    { name: '大理古城', year: 2024, coord: [100.16, 25.69], city: '云南 · 大理', photos: 34,
      blurb: '风花雪月不是成语，是大理的四种天气：下关风、上关花、苍山雪、洱海月。',
      thumbs: ['erhai-village.jpg', 'erhai-pano.jpg', 'erhai-sunset.jpg'], trip: '云南环线：从滇池到玉龙' },
    { name: '洱海', year: 2024, coord: [100.18, 25.75], city: '云南 · 大理', photos: 42,
      blurb: 'S 湾的日落持续了整整四十分钟，云从橘红烧到绛紫，最后沉入墨蓝。没有人说话。',
      thumbs: ['erhai-sunset.jpg', 'erhai-pano.jpg', 'erhai-village.jpg'], trip: '云南环线：从滇池到玉龙' },
    { name: '崇圣寺三塔', year: 2024, coord: [100.15, 25.72], city: '云南 · 大理', photos: 18,
      blurb: '千年三塔立在苍山脚下，哥哥在三塔倒影公园数了很久的塔尖。',
      thumbs: ['erhai-pano.jpg', 'erhai-village.jpg', 'erhai-sunset.jpg'], trip: '云南环线：从滇池到玉龙' },
    { name: '丽江古城', year: 2024, coord: [100.24, 26.87], city: '云南 · 丽江', photos: 27,
      blurb: '狮子山万古楼看整片青瓦屋顶，晚上的四方街有手鼓声。',
      thumbs: ['erhai-village.jpg', 'erhai-sunset.jpg', 'gulls-boy.jpg'], trip: '云南环线：从滇池到玉龙' },
    { name: '玉龙雪山', year: 2024, coord: [100.20, 27.10], city: '云南 · 丽江', photos: 36,
      blurb: '哥哥在缆车里睡着了，醒来推窗见雪："云在我脚下。"他人生第一场真正的雪。',
      thumbs: ['yulong-peak.jpg', 'yulong-trail.jpg', 'snow-family.jpg'], trip: '云南环线：从滇池到玉龙' },
    { name: '四姑娘山 · 双桥沟', year: 2023, coord: [102.90, 31.10], city: '四川 · 阿坝', photos: 52,
      blurb: '翻过巴朗山垭口的那一刻，云海在脚下铺开。夜里的星星多到让人生出敬畏。',
      thumbs: ['stars.jpg', 'ganhaizi.jpg', 'yulong-peak.jpg'], trip: '四姑娘山下的星空' },
    { name: '宽窄巷子', year: 2023, coord: [104.05, 30.66], city: '四川 · 成都', photos: 23,
      blurb: '出发前的一晚，火锅、盖碗茶和采耳，成都负责把旅行的开头调得松弛。',
      thumbs: ['erhai-village.jpg', 'qingdao-tide.jpg', 'erhai-pano.jpg'], trip: '四姑娘山下的星空' },
    { name: '青岛 · 礁石滩', year: 2023, coord: [120.35, 36.05], city: '山东 · 青岛', photos: 61,
      blurb: '退潮后的礁石滩是一座没有围墙的自然博物馆。哥哥蹲了两小时，带回一只寄居蟹。',
      thumbs: ['qingdao-tide.jpg', 'qingdao-beach.jpg', 'snow-family.jpg'], trip: '赶海的小孩' },
    { name: '千岛湖', year: 2022, coord: [119.02, 29.60], city: '浙江 · 杭州', photos: 44,
      blurb: '骑行环湖绿道，跳进湖里的一瞬间，整个夏天都凉了。',
      thumbs: ['erhai-pano.jpg', 'erhai-village.jpg', 'stars.jpg'], trip: '千岛湖的夏天' },
    { name: '故宫', year: 2019, coord: [116.39, 39.91], city: '北京', photos: 88,
      blurb: '哥哥第一次见到真正的宫殿，在太和殿前的广场上跑了三个来回。',
      thumbs: ['erhai-village.jpg', 'yulong-peak.jpg', 'qingdao-beach.jpg'], trip: '胡同与冰糖葫芦' },
    { name: '京都 · 哲学之道', year: 2018, coord: [135.80, 35.03], city: '日本 · 京都', photos: 96,
      blurb: '樱吹雪落了满肩。第一次带哥哥出国，他学会了说 arigatou。',
      thumbs: ['kyoto.jpg', 'kyoto-v.jpg', 'gulls-boy.jpg'], trip: '落樱时节，又逢君' }
  ];

  var TRIPS = [
    { year: 2024, name: '云南环线', coords: [[102.67, 24.98], [100.16, 25.69], [100.24, 26.87], [100.20, 27.10]] },
    { year: 2023, name: '川西小环线', coords: [[104.05, 30.66], [102.90, 31.10]] },
    { year: 2023, name: '青岛赶海', coords: [[120.35, 36.05]] },
    { year: 2022, name: '千岛湖', coords: [[119.02, 29.60]] },
    { year: 2019, name: '北京', coords: [[116.39, 39.91]] },
    { year: 2018, name: '关西', coords: [[135.80, 35.03]] }
  ];

  var PROVINCES = {
    '云南省': 3, '四川省': 2, '浙江省': 2, '山东省': 1, '北京市': 2, '上海市': 3,
    '贵州省': 1, '江苏省': 1, '湖南省': 1, '广东省': 2
  };

  var YEARS = [2024, 2023, 2022, 2019, 2018];
  var currentYear = 'all';

  /* ---------- 地图 ---------- */
  fetch(BASE + 'china.json').then(function (r) { return r.json(); }).then(function (geo) {
    echarts.registerMap('china', geo);
    var chart = echarts.init(document.getElementById('map'), null, { renderer: 'canvas' });

    function spotData(year) {
      return SPOTS.filter(function (s) { return year === 'all' || s.year === year; })
        .map(function (s) {
          return { name: s.name, value: [s.coord[0], s.coord[1], s.photos], spot: s };
        });
    }
    function lineData(year) {
      var out = [];
      TRIPS.filter(function (t) { return year === 'all' || t.year === year; }).forEach(function (t) {
        for (var i = 0; i < t.coords.length - 1; i++) {
          out.push({ coords: [t.coords[i], t.coords[i + 1]] });
        }
      });
      return out;
    }

    chart.setOption({
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(255,255,255,.96)',
        borderColor: '#ECE8E1', textStyle: { color: '#1F2A33', fontSize: 12.5 },
        formatter: function (p) {
          if (p.seriesType === 'effectScatter') {
            var s = p.data.spot;
            return '<b>' + s.name + '</b><br/>' + s.year + ' 年 · ' + s.city + ' · ' + s.photos + ' 张照片<br/><span style="color:#98A1AB">点击查看这里的故事</span>';
          }
          return p.name;
        }
      },
      geo: {
        map: 'china', roam: true, scaleLimit: { min: 1, max: 14 },
        center: [110, 33], zoom: 1.15,
        itemStyle: { borderColor: T.border, borderWidth: 1.2 },
        emphasis: { label: { color: T.label }, itemStyle: { areaColor: T.emphasis } },
        select: { disabled: true }
      },
      series: [
        {
          name: '足迹', type: 'map', map: 'china', geoIndex: 0, selectedMode: false,
          data: Object.keys(PROVINCES).map(function (n) { return { name: n, value: PROVINCES[n] }; })
        },
        {
          name: '景点', type: 'effectScatter', coordinateSystem: 'geo',
          symbolSize: function (v) { return 9 + Math.min(v[2], 60) / 12; },
          itemStyle: { color: T.cityDot, borderColor: '#fff', borderWidth: 2 },
          rippleEffect: { scale: 3, brushType: 'stroke' },
          label: {
            show: true, position: 'top', distance: 7, formatter: function (p) {
              return p.data.spot.name + ' · ' + p.data.spot.year;
            },
            color: '#3E4C57', fontSize: 11, fontWeight: 600,
            backgroundColor: 'rgba(255,255,255,.85)', borderRadius: 6, padding: [2, 7],
            shadowColor: 'rgba(31,42,51,.10)', shadowBlur: 6
          },
          labelLayout: { hideOverlap: true },
          cursor: 'pointer',
          data: spotData('all')
        },
        {
          name: '路线', type: 'lines', coordinateSystem: 'geo',
          effect: { show: true, period: 5, trailLength: 0.5, symbol: 'arrow', symbolSize: 5, color: T.route },
          lineStyle: { color: T.route, width: 1.8, opacity: 0.75, curveness: 0.25 },
          data: lineData('all')
        }
      ]
    });

    /* 点击景点 → 第二幕面板 */
    chart.on('click', function (params) {
      if (params.seriesType === 'effectScatter' && params.data && params.data.spot) {
        openPanel(params.data.spot);
      }
    });

    /* 年份筛选 */
    document.querySelectorAll('.year-dock button').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.year-dock button').forEach(function (b) { b.classList.remove('on'); });
        btn.classList.add('on');
        currentYear = btn.dataset.year === 'all' ? 'all' : parseInt(btn.dataset.year, 10);
        chart.setOption({
          series: [
            {},
            { data: spotData(currentYear) },
            { data: lineData(currentYear) }
          ]
        });
      });
    });

    window.addEventListener('resize', function () { chart.resize(); });
  }).catch(function (e) { console.error('GeoJSON 加载失败', e); });

  /* ---------- 面板 ---------- */
  var panel = document.getElementById('panel');
  var tpl = document.getElementById('panel-tpl');

  function openPanel(spot) {
    if (!panel || !tpl) return;
    var html = tpl.innerHTML
      .replace(/\{IMG\}/g, BASE + 'img/' + spot.thumbs[0])
      .replace(/\{NAME\}/g, spot.name)
      .replace(/\{YEAR\}/g, spot.year)
      .replace(/\{CITY\}/g, spot.city)
      .replace(/\{BLURB\}/g, spot.blurb)
      .replace(/\{TRIP\}/g, spot.trip)
      .replace(/\{T1\}/g, BASE + 'img/' + spot.thumbs[0])
      .replace(/\{T2\}/g, BASE + 'img/' + spot.thumbs[1])
      .replace(/\{T3\}/g, BASE + 'img/' + spot.thumbs[2]);
    panel.innerHTML = html;
    panel.classList.add('open');
    document.getElementById('hint') && document.getElementById('hint').classList.add('gone');
    panel.querySelector('.close').addEventListener('click', function () { panel.classList.remove('open'); });
  }

  /* ---------- 开场帷幕 ---------- */
  var veil = document.getElementById('veil');
  if (veil) {
    veil.querySelector('.go').addEventListener('click', function () {
      veil.classList.add('gone');
      var hint = document.getElementById('hint');
      if (hint) {
        setTimeout(function () { hint.classList.remove('gone'); }, 400);
        setTimeout(function () { hint.classList.add('gone'); }, 7000);
      }
    });
  }
})();
