// Двусторонняя логика % ↔ ₽ на клиенте (визуально), сервер — источник правды
window.rowCalc = ({ base, percent, fixed }) => ({
  base: Number(base) || 0,
  percent: percent ?? null,
  fixed: fixed ?? null,
  syncPercent() {
    // если меняют %, фикс чистим
    if (this.percent !== null && this.percent !== "") {
      this.fixed = null;
    }
  },
  syncFixed() {
    // если меняют ₽, % пересчитываем визуально (чтобы пользователь видел связь)
    if (this.fixed !== null && this.fixed !== "" && this.base > 0) {
      this.percent = (Number(this.fixed) / this.base * 100).toFixed(2);
    } else if (this.fixed !== null && this.fixed !== "") {
      this.percent = null;
    }
  }
});

// mobile bottom sheet
window.bsheet = (() => {
  const el = () => document.getElementById('bottom-sheet');
  return {
    toggle(){ el().classList.toggle('show'); },
    hide(){ el().classList.remove('show'); }
  }
})();