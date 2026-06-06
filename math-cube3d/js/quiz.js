class QuizHelper {
  constructor() {
    this.invalidNets = [
      // 凹字形
      {
        id: 'invalid-ao',
        type: 'invalid',
        rootId: 3,
        faces: {
          3: { id: 3, x: 1, y: 1, parent: null, joint: null },
          2: { id: 2, x: 0, y: 1, parent: 3, joint: 'left' },
          1: { id: 1, x: 0, y: 0, parent: 2, joint: 'top' },
          4: { id: 4, x: 2, y: 1, parent: 3, joint: 'right' },
          5: { id: 5, x: 2, y: 0, parent: 4, joint: 'top' },
          6: { id: 6, x: 1, y: 0, parent: 3, joint: 'top' } // 与 1/5 形成闭环重叠
        }
      },
      // 田字形
      {
        id: 'invalid-tian',
        type: 'invalid',
        rootId: 3,
        faces: {
          3: { id: 3, x: 1, y: 1, parent: null, joint: null },
          2: { id: 2, x: 0, y: 1, parent: 3, joint: 'left' },
          1: { id: 1, x: 0, y: 0, parent: 2, joint: 'top' },
          4: { id: 4, x: 1, y: 0, parent: 3, joint: 'top' },
          5: { id: 5, x: 2, y: 1, parent: 3, joint: 'right' },
          6: { id: 6, x: 2, y: 0, parent: 5, joint: 'top' }
        }
      },
      // 5面非正方体
      {
        id: 'invalid-5faces',
        type: 'invalid',
        rootId: 3,
        faces: {
          3: { id: 3, x: 1, y: 1, parent: null, joint: null },
          2: { id: 2, x: 0, y: 1, parent: 3, joint: 'left' },
          1: { id: 1, x: 0, y: 0, parent: 2, joint: 'top' },
          4: { id: 4, x: 2, y: 1, parent: 3, joint: 'right' },
          5: { id: 5, x: 1, y: 0, parent: 3, joint: 'top' }
        }
      }
    ];
  }

  // 生成混合题集 (10道题)
  generateQuestions() {
    // 随机打乱并分配所有 11 种合法展开图，保证 quiz 内使用不同展开图
    const shuffledValid = [...NETS_DATA].sort(() => Math.random() - 0.5);
    
    const typeAValidNets = [shuffledValid[0], shuffledValid[1]];
    const typeBNets = [shuffledValid[2], shuffledValid[3], shuffledValid[4]];
    const typeCNets = [shuffledValid[5], shuffledValid[6], shuffledValid[7]];
    
    // 随机打乱并分配无效展开图，保证不重复
    const shuffledInvalid = [...this.invalidNets].sort(() => Math.random() - 0.5);
    const typeAInvalidNets = [shuffledInvalid[0], shuffledInvalid[1]];

    const list = [];
    // Q1-Q4: 能否拼合 (2个能，2个不能)
    list.push(this.makeTypeA(true, typeAValidNets[0]));
    list.push(this.makeTypeA(false, typeAInvalidNets[0]));
    list.push(this.makeTypeA(true, typeAValidNets[1]));
    list.push(this.makeTypeA(false, typeAInvalidNets[1]));
    // Q5-Q7: 找对面 (3个)
    list.push(this.makeTypeB(typeBNets[0]));
    list.push(this.makeTypeB(typeBNets[1]));
    list.push(this.makeTypeB(typeBNets[2]));
    // Q8-Q10: 立体匹配 (3个)
    list.push(this.makeTypeC(typeCNets[0]));
    list.push(this.makeTypeC(typeCNets[1]));
    list.push(this.makeTypeC(typeCNets[2]));

    // 打乱题库顺序
    return list.sort(() => Math.random() - 0.5);
  }

  makeTypeA(isValid, net) {
    return {
      type: 'A',
      netData: net,
      questionText: '下面的平面图形能折叠成一个封闭的正方体吗？',
      options: ['能', '不能'],
      correctAnswer: isValid ? '能' : '不能'
    };
  }

  makeTypeB(net) {
    const rootId = net.rootId;
    
    const opposites = {
      '1-4-1-a': { 3: 1, 1: 3, 2: 4, 4: 2, 5: 6, 6: 5 },
      '1-4-1-b': { 3: 1, 1: 3, 2: 4, 4: 2, 5: 6, 6: 5 },
      '1-4-1-c': { 3: 1, 1: 3, 2: 4, 4: 2, 5: 6, 6: 5 },
      '1-4-1-d': { 3: 1, 1: 3, 2: 4, 4: 2, 5: 6, 6: 5 },
      '1-4-1-e': { 3: 1, 1: 3, 2: 4, 4: 2, 5: 6, 6: 5 },
      '1-4-1-f': { 3: 1, 1: 3, 2: 4, 4: 2, 5: 6, 6: 5 },
      '2-3-1-a': { 1: 6, 6: 1, 2: 3, 3: 2, 4: 5, 5: 4 },
      '2-3-1-b': { 1: 6, 6: 1, 2: 3, 3: 2, 4: 5, 5: 4 },
      '2-3-1-c': { 1: 6, 6: 1, 2: 3, 3: 2, 4: 5, 5: 4 },
      '2-2-2': { 3: 6, 6: 3, 2: 5, 5: 2, 1: 4, 4: 1 },
      '3-3': { 1: 3, 3: 1, 2: 5, 5: 2, 4: 6, 6: 4 }
    };

    const map = opposites[net.id] || { 3: 1, 1: 3, 2: 4, 4: 2, 5: 6, 6: 5 };
    const targetOppositeId = map[rootId];

    // 给其他面标记字母 A, B, C, D, E
    const labels = ['A', 'B', 'C', 'D', 'E'];
    const nonRootIds = Object.keys(net.faces).map(Number).filter(id => id !== rootId);
    
    const faceLabels = {};
    faceLabels[rootId] = '？';
    nonRootIds.forEach((id, index) => {
      faceLabels[id] = labels[index];
    });

    const correctAnswerLabel = faceLabels[targetOppositeId];

    return {
      type: 'B',
      netData: net,
      customTextMap: faceLabels,
      questionText: `将此平面图折叠成正方体后，标有黄色“？”的面相对的面是哪一个？`,
      options: labels,
      correctAnswer: correctAnswerLabel,
      targetOppositeId: targetOppositeId,
      rootId: rootId
    };
  }

  getVisibleFaceIds(netId) {
    if (netId.startsWith('1-4-1')) {
      return { front: 3, top: 5, right: 4 };
    } else if (netId.startsWith('2-3-1')) {
      return { front: 3, top: 1, right: 5 };
    } else if (netId === '2-2-2') {
      return { front: 3, top: 1, right: 5 };
    } else if (netId === '3-3') {
      return { front: 3, top: 6, right: 5 };
    }
    return { front: 3, top: 5, right: 4 };
  }

  makeTypeC(net) {
    const visibleIds = this.getVisibleFaceIds(net.id);
    const icons = ['🌟', '🔴', '🔺'];

    // 正确的映射
    const mapCorrect = {};
    mapCorrect[visibleIds.front] = icons[0];
    mapCorrect[visibleIds.top] = icons[1];
    mapCorrect[visibleIds.right] = icons[2];

    // 错误的映射 B (颠倒相邻位置)
    const mapSwapped = {};
    mapSwapped[visibleIds.front] = icons[0];
    mapSwapped[visibleIds.top] = icons[2];
    mapSwapped[visibleIds.right] = icons[1];

    // 错误的映射 C (图案缺失)
    const mapMissing = {};
    mapMissing[visibleIds.front] = icons[0];
    mapMissing[visibleIds.top] = icons[1];
    mapMissing[visibleIds.right] = ''; // 留空，不引入外来图案

    // 组合候选集，然后随机打乱映射关系
    const candidates = [
      { map: mapCorrect, isCorrect: true },
      { map: mapSwapped, isCorrect: false },
      { map: mapMissing, isCorrect: false }
    ];
    const shuffledCandidates = candidates.sort(() => Math.random() - 0.5);

    // 将打乱的映射按顺序绑定给 正方体 A、B、C 选项（保持按钮顺序固定）
    const optionsData = [
      { label: '正方体 A', map: shuffledCandidates[0].map, isCorrect: shuffledCandidates[0].isCorrect },
      { label: '正方体 B', map: shuffledCandidates[1].map, isCorrect: shuffledCandidates[1].isCorrect },
      { label: '正方体 C', map: shuffledCandidates[2].map, isCorrect: shuffledCandidates[2].isCorrect }
    ];

    const correctOption = optionsData.find(o => o.isCorrect);

    return {
      type: 'C',
      netData: net,
      customTextMap: mapCorrect, // 展开图采用正确的相对位置
      questionText: '下面哪一个正方体是由左侧的图案展开图折叠而来的？',
      options: ['正方体 A', '正方体 B', '正方体 C'],
      optionsData: optionsData,
      correctAnswer: correctOption.label
    };
  }
}

class QuizManager {
  constructor(cube, tabQuizId) {
    this.cube = cube;
    this.container = document.getElementById(tabQuizId);
    this.helper = new QuizHelper();
    this.questions = [];
    this.currentIndex = 0;
    this.score = 0;
    this.answers = [];
  }

  startQuiz() {
    this.questions = this.helper.generateQuestions();
    this.currentIndex = 0;
    this.score = 0;
    this.answers = [];
    this.renderQuestion();
  }

  renderQuestion() {
    this.container.innerHTML = '';
    if (this.currentIndex >= this.questions.length) {
      this.renderResult();
      return;
    }

    const q = this.questions[this.currentIndex];
    
    // 在 3D 舞台渲染展开图
    this.cube.renderNet(q.netData, q.customTextMap || null);
    if (q.type === 'B') {
      // 高亮黄色“？”面
      setTimeout(() => {
        const el = document.querySelector(`.face[data-id="${q.rootId}"]`);
        if (el) el.classList.add('highlighted');
      }, 50);
    }

    // 创建答题 HTML
    const quizDiv = document.createElement('div');
    quizDiv.className = 'quiz-box';
    quizDiv.style.cssText = 'display:flex; flex-direction:column; gap:1.2rem;';

    const progress = document.createElement('div');
    progress.style.cssText = 'font-size:13px; color:#718096; font-weight:bold;';
    progress.innerText = `闯关进度: ${this.currentIndex + 1} / 10 | 得分: ${this.score}`;
    quizDiv.appendChild(progress);

    const qText = document.createElement('h3');
    qText.style.margin = '0';
    qText.style.fontSize = '16px';
    qText.innerText = q.questionText;
    quizDiv.appendChild(qText);

    if (q.type === 'C') {
      const miniCubesDiv = document.createElement('div');
      miniCubesDiv.className = 'mini-cubes-container';
      miniCubesDiv.style.cssText = 'display:flex; justify-content:space-around; gap:12px; margin: 12px 0;';
      
      q.optionsData.forEach(opt => {
        const item = document.createElement('div');
        item.style.cssText = 'display:flex; flex-direction:column; align-items:center; gap:6px; flex:1; min-width: 0;';
        
        const viewport = document.createElement('div');
        viewport.className = 'cube-viewport mini-viewport';
        viewport.style.cssText = 'width:100%; height:120px;';
        
        const container = document.createElement('div');
        container.className = 'cube-container';
        viewport.appendChild(container);
        item.appendChild(viewport);
        
        const label = document.createElement('div');
        label.innerText = opt.label;
        label.style.cssText = 'font-weight:bold; font-size:13px; color:#4a5568;';
        item.appendChild(label);
        
        miniCubesDiv.appendChild(item);
        
        // Render the folded mini cube
        setTimeout(() => {
          const miniCube = new Cube3D(container);
          miniCube.renderNet(q.netData, opt.map);
          miniCube.setFoldAngle(90);
        }, 50);
      });
      
      quizDiv.appendChild(miniCubesDiv);
    }

    const optsDiv = document.createElement('div');
    optsDiv.style.cssText = 'display:flex; flex-direction:column; gap:0.6rem;';

    q.options.forEach(opt => {
      const btn = document.createElement('button');
      btn.innerText = opt;
      btn.style.cssText = 'text-align:left; padding:12px 16px; font-size:14px;';
      btn.addEventListener('click', () => this.handleAnswer(opt));
      optsDiv.appendChild(btn);
    });
    quizDiv.appendChild(optsDiv);

    const feedback = document.createElement('div');
    feedback.id = 'quizFeedback';
    feedback.style.cssText = 'font-weight:bold; font-size:14px; min-height:24px; color:#e53e3e;';
    quizDiv.appendChild(feedback);

    const nextBtn = document.createElement('button');
    nextBtn.innerText = '下一关';
    nextBtn.className = 'primary';
    nextBtn.style.display = 'none';
    nextBtn.id = 'btnNextQuiz';
    nextBtn.addEventListener('click', () => {
      this.currentIndex++;
      this.renderQuestion();
    });
    quizDiv.appendChild(nextBtn);

    this.container.appendChild(quizDiv);
  }

  handleAnswer(selectedOpt) {
    const q = this.questions[this.currentIndex];
    const feedback = document.getElementById('quizFeedback');
    const nextBtn = document.getElementById('btnNextQuiz');
    
    // 禁用所有选项按钮
    this.container.querySelectorAll('.quiz-box button:not(.primary)').forEach(btn => {
      btn.disabled = true;
      if (btn.innerText === q.correctAnswer) {
        btn.style.background = '#e6fffa';
        btn.style.borderColor = '#319795';
        btn.style.color = '#319795';
      } else if (btn.innerText === selectedOpt) {
        btn.style.background = '#fff5f5';
        btn.style.borderColor = '#e53e3e';
        btn.style.color = '#e53e3e';
      }
    });

    const isCorrect = (selectedOpt === q.correctAnswer);
    if (isCorrect) {
      this.score += 10;
      feedback.innerText = '🎉 答对了！太棒了！';
      feedback.style.color = '#319795';
    } else {
      feedback.innerText = `❌ 答错了，正确答案是: ${q.correctAnswer}`;
      feedback.style.color = '#e53e3e';
    }

    // 3D 舞台交互反馈验证
    if (q.type === 'A') {
      let angle = 0;
      const interval = setInterval(() => {
        angle += 2;
        this.cube.setFoldAngle(angle);
        if (angle >= 90) {
          clearInterval(interval);
        }
      }, 15);
    } else if (q.type === 'B') {
      let angle = 0;
      const interval = setInterval(() => {
        angle += 2;
        this.cube.setFoldAngle(angle);
        if (angle >= 90) {
          clearInterval(interval);
          setTimeout(() => {
            const elOpposite = document.querySelector(`.face[data-id="${q.targetOppositeId}"]`);
            if (elOpposite) elOpposite.classList.add('highlighted');
          }, 100);
        }
      }, 15);
    } else if (q.type === 'C') {
      let angle = 0;
      const interval = setInterval(() => {
        angle += 2;
        this.cube.setFoldAngle(angle);
        if (angle >= 90) {
          clearInterval(interval);
          this.cube.rotationX = -20;
          this.cube.rotationY = 35;
          this.cube.updateTransform();
        }
      }, 15);
    }

    nextBtn.style.display = 'block';
  }

  renderResult() {
    this.container.innerHTML = '';
    const resultDiv = document.createElement('div');
    resultDiv.className = 'result-box';
    resultDiv.style.cssText = 'text-align:center; display:flex; flex-direction:column; gap:1.5rem; padding: 2rem 0;';

    let medal = '🥉 几何初学者';
    if (this.score === 100) medal = '👑 空间魔法师！(满分突破)';
    else if (this.score >= 80) medal = '🥇 空间探险家';
    else if (this.score >= 60) medal = '🥈 几何追寻者';

    resultDiv.innerHTML = `
      <h2 style="margin:0; font-size:24px;">闯关结束！</h2>
      <div style="font-size:48px; font-weight:bold; color:#3b82f6;">${this.score} <span style="font-size:20px; color:#718096;">分</span></div>
      <div style="font-size:18px; font-weight:bold; color:#4a5568;">荣获勋章: <br><span style="color:#dd6b20; font-size:20px; display:inline-block; margin-top:8px;">${medal}</span></div>
      <button class="primary" id="btnRestartQuiz" style="margin-top:1rem; align-self:center;">再来一次</button>
    `;

    this.container.appendChild(resultDiv);
    document.getElementById('btnRestartQuiz').addEventListener('click', () => this.startQuiz());
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { QuizHelper, QuizManager };
}
