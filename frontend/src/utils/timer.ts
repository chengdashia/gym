// 通用倒计时（基于 setInterval）
export type TimerCallback = (remaining: number, total: number) => void;
export type TimerDoneCallback = () => void;

export interface TimerInstance {
  start: (seconds: number) => void;
  pause: () => void;
  resume: () => void;
  skip: () => void;
  adjust: (delta: number) => void;
  stop: () => void;
  getRemaining: () => number;
  getTotal: () => number;
  isRunning: () => boolean;
}

export function createTimer(onTick: TimerCallback, onDone: TimerDoneCallback): TimerInstance {
  let total = 0;
  let remaining = 0;
  let timerId: any = null;
  let running = false;

  function clear() {
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
    running = false;
  }

  function tick() {
    if (remaining <= 0) {
      clear();
      onTick(0, total);
      onDone();
      return;
    }
    onTick(remaining, total);
    if (running) {
      remaining -= 1;
    }
  }

  return {
    start(seconds) {
      total = seconds;
      remaining = seconds;
      clear();
      running = true;
      tick();
      timerId = setInterval(tick, 1000);
    },
    pause() {
      running = false;
    },
    resume() {
      if (remaining > 0 && !running) running = true;
    },
    skip() {
      remaining = 0;
      clear();
      onTick(0, total);
      onDone();
    },
    adjust(delta) {
      remaining = Math.max(0, remaining + delta);
      total = Math.max(total + delta, remaining);
      if (!timerId && remaining > 0) {
        running = true;
        tick();
        timerId = setInterval(tick, 1000);
      }
    },
    stop() {
      clear();
    },
    getRemaining: () => remaining,
    getTotal: () => total,
    isRunning: () => running,
  };
}