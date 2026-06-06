const NETS_DATA = [
  // 1-4-1型 (6种)
  {
    id: '1-4-1-a',
    type: '1-4-1',
    name: '1-4-1型-方案A',
    rootId: 3,
    faces: {
      3: { id: 3, x: 2, y: 1, parent: null, joint: null }, // 底面
      2: { id: 2, x: 1, y: 1, parent: 3, joint: 'left' },
      1: { id: 1, x: 0, y: 1, parent: 2, joint: 'left' },
      4: { id: 4, x: 3, y: 1, parent: 3, joint: 'right' },
      5: { id: 5, x: 2, y: 0, parent: 3, joint: 'top' }, // 顶盖面
      6: { id: 6, x: 2, y: 2, parent: 3, joint: 'bottom' }
    }
  },
  {
    id: '1-4-1-b',
    type: '1-4-1',
    name: '1-4-1型-方案B',
    rootId: 3,
    faces: {
      3: { id: 3, x: 2, y: 1, parent: null, joint: null },
      2: { id: 2, x: 1, y: 1, parent: 3, joint: 'left' },
      1: { id: 1, x: 0, y: 1, parent: 2, joint: 'left' },
      4: { id: 4, x: 3, y: 1, parent: 3, joint: 'right' },
      5: { id: 5, x: 1, y: 0, parent: 2, joint: 'top' },
      6: { id: 6, x: 2, y: 2, parent: 3, joint: 'bottom' }
    }
  },
  {
    id: '1-4-1-c',
    type: '1-4-1',
    name: '1-4-1型-方案C',
    rootId: 3,
    faces: {
      3: { id: 3, x: 2, y: 1, parent: null, joint: null },
      2: { id: 2, x: 1, y: 1, parent: 3, joint: 'left' },
      1: { id: 1, x: 0, y: 1, parent: 2, joint: 'left' },
      4: { id: 4, x: 3, y: 1, parent: 3, joint: 'right' },
      5: { id: 5, x: 0, y: 0, parent: 1, joint: 'top' },
      6: { id: 6, x: 2, y: 2, parent: 3, joint: 'bottom' }
    }
  },
  {
    id: '1-4-1-d',
    type: '1-4-1',
    name: '1-4-1型-方案D',
    rootId: 3,
    faces: {
      3: { id: 3, x: 2, y: 1, parent: null, joint: null },
      2: { id: 2, x: 1, y: 1, parent: 3, joint: 'left' },
      1: { id: 1, x: 0, y: 1, parent: 2, joint: 'left' },
      4: { id: 4, x: 3, y: 1, parent: 3, joint: 'right' },
      5: { id: 5, x: 2, y: 0, parent: 3, joint: 'top' },
      6: { id: 6, x: 1, y: 2, parent: 2, joint: 'bottom' }
    }
  },
  {
    id: '1-4-1-e',
    type: '1-4-1',
    name: '1-4-1型-方案E',
    rootId: 3,
    faces: {
      3: { id: 3, x: 2, y: 1, parent: null, joint: null },
      2: { id: 2, x: 1, y: 1, parent: 3, joint: 'left' },
      1: { id: 1, x: 0, y: 1, parent: 2, joint: 'left' },
      4: { id: 4, x: 3, y: 1, parent: 3, joint: 'right' },
      5: { id: 5, x: 2, y: 0, parent: 3, joint: 'top' },
      6: { id: 6, x: 0, y: 2, parent: 1, joint: 'bottom' }
    }
  },
  {
    id: '1-4-1-f',
    type: '1-4-1',
    name: '1-4-1型-方案F',
    rootId: 3,
    faces: {
      3: { id: 3, x: 2, y: 1, parent: null, joint: null },
      2: { id: 2, x: 1, y: 1, parent: 3, joint: 'left' },
      1: { id: 1, x: 0, y: 1, parent: 2, joint: 'left' },
      4: { id: 4, x: 3, y: 1, parent: 3, joint: 'right' },
      5: { id: 5, x: 1, y: 0, parent: 2, joint: 'top' },
      6: { id: 6, x: 1, y: 2, parent: 2, joint: 'bottom' }
    }
  },
  // 2-3-1型 (3种)
  {
    id: '2-3-1-a',
    type: '2-3-1',
    name: '2-3-1型-方案A',
    rootId: 3,
    faces: {
      "1": { "id": 1, "x": 2, "y": 0, "parent": 5, "joint": "top" },
      "2": { "id": 2, "x": 3, "y": 0, "parent": 1, "joint": "right" },
      "3": { "id": 3, "x": 1, "y": 1, "parent": null, "joint": null },
      "4": { "id": 4, "x": 0, "y": 1, "parent": 3, "joint": "left" },
      "5": { "id": 5, "x": 2, "y": 1, "parent": 3, "joint": "right" },
      "6": { "id": 6, "x": 0, "y": 2, "parent": 4, "joint": "bottom" }
    }
  },
  {
    id: '2-3-1-b',
    type: '2-3-1',
    name: '2-3-1型-方案B',
    rootId: 3,
    faces: {
      "1": { "id": 1, "x": 2, "y": 0, "parent": 5, "joint": "top" },
      "2": { "id": 2, "x": 3, "y": 0, "parent": 1, "joint": "right" },
      "3": { "id": 3, "x": 1, "y": 1, "parent": null, "joint": null },
      "4": { "id": 4, "x": 0, "y": 1, "parent": 3, "joint": "left" },
      "5": { "id": 5, "x": 2, "y": 1, "parent": 3, "joint": "right" },
      "6": { "id": 6, "x": 1, "y": 2, "parent": 3, "joint": "bottom" }
    }
  },
  {
    id: '2-3-1-c',
    type: '2-3-1',
    name: '2-3-1型-方案C',
    rootId: 3,
    faces: {
      "1": { "id": 1, "x": 2, "y": 0, "parent": 5, "joint": "top" },
      "2": { "id": 2, "x": 3, "y": 0, "parent": 1, "joint": "right" },
      "3": { "id": 3, "x": 1, "y": 1, "parent": null, "joint": null },
      "4": { "id": 4, "x": 0, "y": 1, "parent": 3, "joint": "left" },
      "5": { "id": 5, "x": 2, "y": 1, "parent": 3, "joint": "right" },
      "6": { "id": 6, "x": 2, "y": 2, "parent": 5, "joint": "bottom" }
    }
  },
  // 2-2-2型 (1种)
  {
    id: '2-2-2',
    type: '2-2-2',
    name: '2-2-2型',
    rootId: 3,
    faces: {
      3: { id: 3, x: 1, y: 1, parent: null, joint: null },
      2: { id: 2, x: 0, y: 1, parent: 3, joint: 'left' },
      1: { id: 1, x: 0, y: 0, parent: 2, joint: 'top' },
      4: { id: 4, x: 1, y: 2, parent: 3, joint: 'bottom' },
      5: { id: 5, x: 2, y: 2, parent: 4, joint: 'right' },
      6: { id: 6, x: 2, y: 3, parent: 5, joint: 'bottom' }
    }
  },
  // 3-3型 (1种)
  {
    id: '3-3',
    type: '3-3',
    name: '3-3型',
    rootId: 3,
    faces: {
      "1": { "id": 1, "x": 0, "y": 0, "parent": 2, "joint": "left" },
      "2": { "id": 2, "x": 1, "y": 0, "parent": 3, "joint": "left" },
      "3": { "id": 3, "x": 2, "y": 0, "parent": null, "joint": null },
      "4": { "id": 4, "x": 2, "y": 1, "parent": 3, "joint": "bottom" },
      "5": { "id": 5, "x": 3, "y": 1, "parent": 4, "joint": "right" },
      "6": { "id": 6, "x": 4, "y": 1, "parent": 5, "joint": "right" }
    }
  }
];

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { NETS_DATA };
}
