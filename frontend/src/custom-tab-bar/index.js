// SVG 图标 data URI 生成（内联，不依赖打包，原生组件直接用）
function iconSrc(name, color, sw) {
  var strokeWidth = sw || 1.8;
  var paths = {
    home: '<path d="M3 10.5L12 3l9 7.5"/><path d="M5 9.5V20h5v-6h4v6h5V9.5"/>',
    diet: '<path d="M5 11a7 7 0 0 0 14 0"/><path d="M3 11h18"/><path d="M9 11V8a3 3 0 0 1 6 0v3"/><path d="M12 21v-3"/>',
    training: '<path d="M6.5 8v8"/><path d="M17.5 8v8"/><path d="M3.5 10v4"/><path d="M20.5 10v4"/><path d="M6.5 12h11"/>',
    stats: '<path d="M4 20h16"/><path d="M7 20v-7"/><path d="M12 20V8"/><path d="M17 20v-12"/>',
    mine: '<circle cx="12" cy="8" r="4"/><path d="M5 20c0-3.5 3-6 7-6s7 2.5 7 6"/>',
  };
  var inner = paths[name] || '';
  if (!inner) return '';
  var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="' + color + '" stroke-width="' + strokeWidth + '" stroke-linecap="round" stroke-linejoin="round">' + inner + '</svg>';
  return 'data:image/svg+xml,' + encodeURIComponent(svg);
}

var INACTIVE_COLOR = '#8FA3A1';
var ACTIVE_COLOR = '#FFFFFF';

Component({
  data: {
    activeIdx: 0,
    ready: false,
    navigating: false,
    list: [
      { pagePath: '/pages/home/index',     text: '首页', icon: 'home',     inactive: '', active: '' },
      { pagePath: '/pages/diet/index',     text: '饮食', icon: 'diet',     inactive: '', active: '' },
      { pagePath: '/pages/training/index', text: '训练', icon: 'training', inactive: '', active: '' },
      { pagePath: '/pages/stats/index',    text: '数据', icon: 'stats',    inactive: '', active: '' },
      { pagePath: '/pages/mine/index',     text: '我的', icon: 'mine',     inactive: '', active: '' },
    ],
  },

  lifetimes: {
    attached() {
      // 预生成所有图标的 data URI
      var list = this.data.list.map(function (item) {
        return {
          pagePath: item.pagePath,
          text: item.text,
          icon: item.icon,
          inactive: iconSrc(item.icon, INACTIVE_COLOR, 1.7),
          active: iconSrc(item.icon, ACTIVE_COLOR, 2.0),
        };
      });
      var pages = getCurrentPages();
      var route = pages.length ? (pages[pages.length - 1].route || '') : '';
      var idx = list.findIndex(function (item) {
        var p = item.pagePath.charAt(0) === '/' ? item.pagePath.slice(1) : item.pagePath;
        return route === p;
      });
      // Initialize route and icon data in a single render.  Rendering at index
      // 0 first makes the pill visibly sweep across unrelated tabs on device.
      this.setData({ list: list, activeIdx: idx === -1 ? 0 : idx, ready: true });
    },
  },

  pageLifetimes: {
    show() {
      this.syncActive();
    },
  },

  methods: {
    syncActive() {
      var pages = getCurrentPages();
      if (!pages.length) return;
      var route = pages[pages.length - 1].route || '';
      var idx = this.data.list.findIndex(function (item) {
        var p = item.pagePath.charAt(0) === '/' ? item.pagePath.slice(1) : item.pagePath;
        return route === p;
      });
      if (idx !== -1 && idx !== this.data.activeIdx) {
        this.setData({ activeIdx: idx });
      }
    },

    onSwitch(e) {
      var idx = e.currentTarget.dataset.idx;
      if (idx === this.data.activeIdx || this.data.navigating) return;
      var item = this.data.list[idx];
      this.setData({ navigating: true, activeIdx: idx });
      wx.switchTab({
        url: item.pagePath,
        success: () => this.syncActive(),
        complete: () => this.setData({ navigating: false }),
      });
    },
  },
});
