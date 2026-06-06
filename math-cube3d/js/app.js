document.addEventListener('DOMContentLoaded', () => {
  const cube = new Cube3D('cubeContainer');
  let autoPlayInterval = null;
  let isPlaying = false;

  // 绑定基础控制栏
  const btnPlay = document.getElementById('btnPlay');
  const foldSlider = document.getElementById('foldSlider');
  const btnResetView = document.getElementById('btnResetView');

  const updatePlayState = (playing) => {
    isPlaying = playing;
    btnPlay.innerText = isPlaying ? '暂停' : '播放';
    if (isPlaying) {
      autoPlayInterval = setInterval(() => {
        let val = parseInt(foldSlider.value) + 1;
        if (val > 90) {
          val = 0; // 循环播放
        }
        foldSlider.value = val;
        cube.setFoldAngle(val);
      }, 30);
    } else {
      clearInterval(autoPlayInterval);
    }
  };

  btnPlay.addEventListener('click', () => updatePlayState(!isPlaying));
  foldSlider.addEventListener('input', () => {
    updatePlayState(false);
    cube.setFoldAngle(parseInt(foldSlider.value));
  });
  btnResetView.addEventListener('click', () => cube.resetView());

  // Tabs 切换逻辑
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabDemo = document.getElementById('tabDemo');
  const tabQuiz = document.getElementById('tabQuiz');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      updatePlayState(false);
      foldSlider.value = 0;
      cube.setFoldAngle(0);

      if (btn.dataset.tab === 'demo') {
        tabDemo.classList.remove('hidden');
        tabQuiz.classList.add('hidden');
        // 重新载入当前的示范展开图
        loadDemoNet();
      } else {
        tabDemo.classList.add('hidden');
        tabQuiz.classList.remove('hidden');
        if (window.quizManager) {
          window.quizManager.startQuiz();
        }
      }
    });
  });

  // 教学演示展开图生成
  const loadDemoNet = () => {
    const activeThumb = tabDemo.querySelector('.net-thumb.active');
    if (activeThumb) {
      const netId = activeThumb.dataset.id;
      const netData = NETS_DATA.find(n => n.id === netId);
      if (netData) {
        cube.renderNet(netData);
      }
    }
  };

  const initDemoTab = () => {
    tabDemo.innerHTML = '';
    const categories = [
      { type: '1-4-1', name: '“1-4-1”型展开图' },
      { type: '2-3-1', name: '“2-3-1”型展开图' },
      { type: '2-2-2', name: '“2-2-2”型展开图' },
      { type: '3-3', name: '“3-3”型展开图' }
    ];

    categories.forEach(cat => {
      const sect = document.createElement('div');
      sect.className = 'net-category';
      
      const title = document.createElement('div');
      title.className = 'net-category-title';
      title.innerText = cat.name;
      sect.appendChild(title);

      const grid = document.createElement('div');
      grid.className = 'net-grid';

      const list = NETS_DATA.filter(n => n.type === cat.type);
      list.forEach((net, index) => {
        const thumb = document.createElement('div');
        thumb.className = 'net-thumb';
        thumb.dataset.id = net.id;
        thumb.innerText = `${cat.type} #${index + 1}`;
        
        thumb.addEventListener('click', () => {
          tabDemo.querySelectorAll('.net-thumb').forEach(t => t.classList.remove('active'));
          thumb.classList.add('active');
          updatePlayState(false);
          foldSlider.value = 0;
          cube.renderNet(net);
        });
        grid.appendChild(thumb);
      });

      sect.appendChild(grid);
      tabDemo.appendChild(sect);
    });

    // 默认选中第一个
    const firstThumb = tabDemo.querySelector('.net-thumb');
    if (firstThumb) {
      firstThumb.classList.add('active');
      loadDemoNet();
    }
  };

  initDemoTab();
  window.cubeInstance = cube;
  window.quizManager = new QuizManager(cube, 'tabQuiz');
});
