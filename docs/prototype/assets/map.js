/* up-journey 原型 · 地图渲染（ECharts，数据为假数据） */
(function () {
  var ACCENT = '#2F4A5C';

  function loadChina(cb) {
    fetch('assets/china.json')
      .then(function (r) { return r.json(); })
      .then(cb)
      .catch(function (e) { console.error('GeoJSON 加载失败', e); });
  }

  /* ---------- 足迹总览大地图 ---------- */
  var mapEl = document.getElementById('map');
  if (mapEl) {
    loadChina(function (geo) {
      echarts.registerMap('china', geo);

      var visited = {
        '云南省': 3, '四川省': 2, '贵州省': 1, '浙江省': 2, '江苏省': 1,
        '山东省': 1, '湖南省': 1, '广东省': 2, '北京市': 2, '上海市': 3
      };
      var data = Object.keys(visited).map(function (name) {
        return { name: name, value: visited[name] };
      });

      var cities = [
        { name: '昆明', value: [102.83, 24.88, 3] },
        { name: '大理', value: [100.23, 25.60, 2] },
        { name: '丽江', value: [100.24, 26.87, 1] },
        { name: '成都', value: [104.07, 30.67, 2] },
        { name: '杭州', value: [120.16, 30.29, 2] },
        { name: '青岛', value: [120.38, 36.07, 1] },
        { name: '北京', value: [116.40, 39.90, 2] },
        { name: '上海', value: [121.47, 31.23, 3] },
        { name: '广州', value: [113.26, 23.13, 1] }
      ];

      var chart = echarts.init(mapEl);
      chart.setOption({
        tooltip: { trigger: 'item' },
        visualMap: {
          type: 'piecewise',
          pieces: [
            { gt: 2, label: '去过 3 次以上', color: '#243A49' },
            { gt: 1, lte: 2, label: '去过 2 次', color: '#3D5D72' },
            { gt: 0, lte: 1, label: '去过 1 次', color: '#7A94A5' },
            { value: 0, label: '还没去过', color: '#EFECE5' }
          ],
          left: 16,
          bottom: 24,
          itemWidth: 12,
          itemHeight: 12,
          textStyle: { color: '#8A8378', fontSize: 11 },
          selectedMode: false
        },
        geo: {
          map: 'china',
          roam: true,
          scaleLimit: { min: 1, max: 8 },
          itemStyle: { borderColor: '#FAF9F6', borderWidth: 1 },
          emphasis: { label: { color: '#1A1A1A' }, itemStyle: { areaColor: '#D8E2E9' } }
        },
        series: [
          {
            name: '足迹',
            type: 'map',
            map: 'china',
            geoIndex: 0,
            data: data
          },
          {
            name: '城市',
            type: 'effectScatter',
            coordinateSystem: 'geo',
            symbolSize: function (v) { return 6 + v[2] * 2; },
            itemStyle: { color: '#B0532F' },
            rippleEffect: { scale: 2.6, brushType: 'stroke' },
            label: {
              show: true, position: 'right', distance: 6,
              formatter: '{b}', color: '#45413C', fontSize: 11,
              fontFamily: 'Songti SC, serif'
            },
            labelLayout: { hideOverlap: true },
            data: cities.map(function (c) {
              return { name: c.name, value: c.value };
            })
          },
          {
            name: '2024 云南环线',
            type: 'lines',
            coordinateSystem: 'geo',
            effect: { show: true, period: 5, trailLength: 0.4, symbol: 'arrow', symbolSize: 6, color: '#B0532F' },
            lineStyle: { color: '#B0532F', width: 1.4, opacity: 0.7, curveness: 0.25 },
            data: [
              { coords: [[102.83, 24.88], [100.23, 25.60]] },
              { coords: [[100.23, 25.60], [100.24, 26.87]] }
            ]
          }
        ]
      });
      window.addEventListener('resize', function () { chart.resize(); });
    });
  }

  /* ---------- 旅行详情 · 景点级小地图 ---------- */
  var miniEl = document.getElementById('mini-map');
  if (miniEl) {
    loadChina(function (geo) {
      echarts.registerMap('china', geo);
      var chart = echarts.init(miniEl);

      var spots = [
        { name: '昆明 · 滇池', value: [102.67, 24.98] },
        { name: '大理古城', value: [100.16, 25.69] },
        { name: '洱海', value: [100.18, 25.75] },
        { name: '崇圣寺三塔', value: [100.15, 25.72] },
        { name: '丽江古城', value: [100.24, 26.87] },
        { name: '玉龙雪山', value: [100.20, 27.10] }
      ];

      chart.setOption({
        tooltip: { trigger: 'item' },
        geo: {
          map: 'china',
          center: [100.6, 25.9],
          zoom: 7,
          roam: true,
          scaleLimit: { min: 5, max: 18 },
          itemStyle: {
            areaColor: '#EFECE5',
            borderColor: '#FAF9F6', borderWidth: 1
          },
          emphasis: { label: { show: true, color: '#8A8378' }, itemStyle: { areaColor: '#D8E2E9' } }
        },
        series: [
          {
            name: '景点',
            type: 'scatter',
            coordinateSystem: 'geo',
            symbolSize: 10,
            itemStyle: { color: ACCENT },
            label: {
              show: true, position: 'top', distance: 8,
              formatter: '{b}', color: '#1A1A1A', fontSize: 12,
              fontFamily: 'Songti SC, serif', fontWeight: 600
            },
            labelLayout: { hideOverlap: true },
            data: spots
          },
          {
            name: '路线',
            type: 'lines',
            coordinateSystem: 'geo',
            lineStyle: { color: ACCENT, width: 1.6, opacity: 0.75, curveness: 0.2, type: 'dashed' },
            effect: { show: true, period: 4, trailLength: 0.5, symbol: 'arrow', symbolSize: 6, color: ACCENT },
            data: [
              { coords: [[102.67, 24.98], [100.16, 25.69]] },
              { coords: [[100.16, 25.69], [100.15, 25.72]] },
              { coords: [[100.15, 25.72], [100.18, 25.75]] },
              { coords: [[100.18, 25.75], [100.24, 26.87]] },
              { coords: [[100.24, 26.87], [100.20, 27.10]] }
            ]
          }
        ]
      });
      window.addEventListener('resize', function () { chart.resize(); });
    });
  }
})();
