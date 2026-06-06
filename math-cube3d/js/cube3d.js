class Cube3D {
  constructor(containerId) {
    this.container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
    this.currentAngle = 0;
    this.rotationX = -30;
    this.rotationY = 45;
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;
    this.initOrbitControls();
  }

  // 初始化拖拽控制
  initOrbitControls() {
    const viewport = this.container.parentElement;

    const onStart = (e) => {
      this.isDragging = true;
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      this.startX = clientX;
      this.startY = clientY;
    };

    const onMove = (e) => {
      if (!this.isDragging) return;
      const clientX = e.touches ? e.touches[0].clientX : e.clientX;
      const clientY = e.touches ? e.touches[0].clientY : e.clientY;
      const deltaX = clientX - this.startX;
      const deltaY = clientY - this.startY;

      this.rotationY += deltaX * 0.5;
      this.rotationX = Math.max(-60, Math.min(60, this.rotationX - deltaY * 0.5));

      this.startX = clientX;
      this.startY = clientY;
      this.updateTransform();
    };

    const onEnd = () => { this.isDragging = false; };

    viewport.addEventListener('mousedown', onStart);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onEnd);

    viewport.addEventListener('touchstart', onStart);
    window.addEventListener('touchmove', onMove);
    window.addEventListener('touchend', onEnd);
  }

  updateTransform() {
    this.container.style.transform = `rotateX(${this.rotationX}deg) rotateY(${this.rotationY}deg)`;
  }

  resetView() {
    this.rotationX = -30;
    this.rotationY = 45;
    this.updateTransform();
  }

  setFoldAngle(angle) {
    this.currentAngle = angle;
    this.container.style.setProperty('--fold-angle', angle);
  }

  // 构建嵌套 DOM 树的核心算法
  renderNet(netData, customTextMap = null) {
    this.container.innerHTML = '';
    this.setFoldAngle(0);

    const faces = netData.faces;
    const rootId = netData.rootId;

    // 递归构建嵌套节点
    const buildTree = (faceId) => {
      const face = faces[faceId];
      const el = document.createElement('div');
      el.className = 'face';
      el.setAttribute('data-id', face.id);

      if (face.parent !== null) {
        el.classList.add(`joint-${face.joint}`);
      } else {
        el.classList.add('root');
        // 根节点定位居中
        el.style.left = '0';
        el.style.top = '0';
      }

      const inner = document.createElement('div');
      inner.className = 'face-inner';
      // 如果有自定义内容贴图，显示自定义内容，否则默认显示面ID
      inner.innerText = customTextMap ? (customTextMap[face.id] || '') : face.id;
      el.appendChild(inner);

      // 寻找所有 parent 为当前面 id 的子面并递归嵌套
      Object.keys(faces).forEach(id => {
        const child = faces[id];
        if (child.parent === faceId) {
          el.appendChild(buildTree(child.id));
        }
      });

      return el;
    };

    const rootDom = buildTree(rootId);
    this.container.appendChild(rootDom);
    this.resetView();
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Cube3D };
}
