// 六卡体检：cards.html 的 #c1..#c6 每张应为 1242×1656，纵向溢出=0、横向溢出元素=0
// 用法：cd <项目根> && hypit capture run <skill>/scripts/check-cards.mjs --channel chrome
// cards.html 定位（取第一个存在）：<CWD>/.github-cards/cards.html（fetch-weekly 新产物）→
// <CWD>/assets/cards/cards.html（旧工作目录布局）→ 脚本相对 ../assets/cards/cards.html
// 结果全走文本 log（勿逐张读图）；任一非 0 → 抛错，禁止出图

import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const CARD_W = 1242;
const CARD_H = 1656;
const TOL = 1; // 亚像素容差

export default async ({ page, log }) => {
  const candidates = [
    resolve(process.cwd(), '.github-cards/cards.html'),
    resolve(process.cwd(), 'assets/cards/cards.html'),
    new URL('../assets/cards/cards.html', import.meta.url).pathname,
  ];
  const target = candidates.find((p) => existsSync(p));
  if (!target) throw new Error('check-cards: 找不到 cards.html（试过 .github-cards/、assets/cards/、脚本相对路径）');
  const url = `file://${encodeURI(target)}`;
  log(`体检对象: ${target}`);
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
