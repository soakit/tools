const test = require('node:test');
const assert = require('node:assert');

test('测试基建工作正常', () => {
  assert.strictEqual(1 + 1, 2);
});

test('加载 11 种展开图并验证数据完整性', () => {
  const { NETS_DATA } = require('../js/nets-data.js');
  assert.strictEqual(NETS_DATA.length, 11);
  NETS_DATA.forEach((net, index) => {
    assert.ok(net.id, `展开图 #${index} 缺少 id`);
    assert.ok(net.type, `展开图 #${index} 缺少分类 type`);
    assert.strictEqual(Object.keys(net.faces).length, 6, `展开图 #${net.id} 必须恰好有 6 个面`);
  });
});

test('验证铰链树构建逻辑', () => {
  const { NETS_DATA } = require('../js/nets-data.js');
  
  // 验证每个展开图的所有面都能通过父子关系链接 to 根节点
  NETS_DATA.forEach(net => {
    const visited = new Set();
    const checkFace = (faceId) => {
      visited.add(faceId);
      Object.keys(net.faces).forEach(id => {
        const f = net.faces[id];
        if (f.parent === faceId) {
          checkFace(f.id);
        }
      });
    };
    checkFace(net.rootId);
    assert.strictEqual(visited.size, 6, `展开图 ${net.id} 的树有孤立面`);
  });
});

test('验证混合练习题生成器', () => {
  const { NETS_DATA } = require('../js/nets-data.js');
  global.NETS_DATA = NETS_DATA; // 模拟浏览器全局变量
  const { QuizHelper } = require('../js/quiz.js');

  const helper = new QuizHelper();
  const questions = helper.generateQuestions();
  assert.strictEqual(questions.length, 10, '生成题集必须是 10 道关卡');
  
  questions.forEach((q, index) => {
    assert.ok(q.type, `第 ${index} 题缺少类型`);
    assert.ok(q.questionText, `第 ${index} 题缺少题干`);
    assert.ok(q.options && q.options.length > 0, `第 ${index} 题缺少选项`);
    assert.ok(q.correctAnswer !== undefined, `第 ${index} 题缺少答案`);
  });
});
