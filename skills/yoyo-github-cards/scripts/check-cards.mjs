// 六卡体检：cards.html 的 #c1..#c6 每张应为 1242×1656，纵向溢出=0、横向溢出元素=0
// 用法：cd <工作目录> && hypit capture run scripts/check-cards.mjs --channel chrome
// 结果全走文本 log（勿逐张读图）；任一非 0 → 抛错，禁止出图
// 脚本相对自身定位 ../assets/cards/cards.html，与工作目录结构绑定

const CARD_W = 1242;
const CARD_H = 1656;
const TOL = 1; // 亚像素容差

export default async ({ page, log }) => {
  const url = new URL('../assets/cards/cards.html', import.meta.url).href;
  await page.setViewport({ width: CARD_W, height: CARD_H });
  await page.goto(url, { waitUntil: 'load' });

  const bad = [];
  for (let i = 1; i <= 6; i++) {
    const id = `c${i}`;
    const r = await page.evaluate(
      (sel, w, h, tol) => {
        const el = document.getElementById(sel);
        if (!el) return { missing: true };
        const box = el.getBoundingClientRect();
        const vertical = Math.max(0, Math.ceil(el.scrollHeight - h));
        const wide = [...el.querySelectorAll('*')].filter((c) => {
          const b = c.getBoundingClientRect();
          if (b.width === 0 && b.height === 0) return false;
          const cs = getComputedStyle(c);
          if (cs.display === 'none' || cs.visibility === 'hidden') return false;
          return b.right - box.right > tol || box.left - b.left > tol;
        }).length;
        return { missing: false, bw: Math.round(box.width), bh: Math.round(box.height), vertical, wide };
      },
      id, CARD_W, CARD_H, TOL,
    );
    if (r.missing) {
      log(`${id} section 缺失`);
      bad.push(id);
      continue;
    }
    log(`${id} 尺寸=${r.bw}x${r.bh} 纵向溢出=${r.vertical} 横向溢出元素=${r.wide}`);
    if (r.vertical !== 0 || r.wide !== 0 || r.bw !== CARD_W || r.bh !== CARD_H) bad.push(id);
  }

  if (bad.length) {
    log(`体检未通过（${bad.length}/6）：${bad.join(', ')} → 先修 cards.html 再出图`);
    throw new Error(`check-cards: ${bad.join(', ')} 未全 0`);
  }
  log('体检通过：6 卡尺寸=1242x1656、纵向溢出=0、横向溢出元素=0');
};
