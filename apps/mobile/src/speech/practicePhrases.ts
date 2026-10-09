// Text only: every selection goes through the same target preparation as typed text.
export const practicePhrases = [
  '我不知道', '你今天忙吗', '我想喝咖啡', '我想买这个', '你吃饭了吗',
  '今天天气很好', '我明天去北京', '你喜欢什么', '我们走吧', '我有点累',
  '请再说一遍', '请说慢一点', '这个多少钱', '洗手间在哪里', '我听不懂',
  '现在几点了', '你住在哪里', '我在学中文', '很高兴认识你', '明天见',
  '我想喝水', '请给我菜单', '我不要太辣', '这个很好吃', '我已经吃过了',
  '我们一起吃饭吧', '我喜欢吃面条', '你想喝什么', '我想喝热茶', '请给我一杯水',
  '我坐地铁去', '车站在哪里', '这里可以坐吗', '我想去超市', '我们几点出发',
  '我快到了', '请等一下', '今天有点冷', '外面下雨了', '记得带雨伞',
  '我明天有空', '周末你想做什么', '我们去散步吧', '我喜欢听音乐', '你会做饭吗',
  '我正在看书', '这本书很有意思', '我每天都练习', '今天我很开心', '我想休息一下',
  '我来帮你', '谢谢你的帮助', '没关系', '我也这么想', '可以再试一次吗',
  '我忘了带手机', '我的手机没电了', '这里有网络吗', '可以用手机付款吗', '我需要一个袋子',
] as const;

export function choosePracticePhrase(previous?: string, random: () => number = Math.random): string {
  const choices = practicePhrases.filter(phrase => phrase !== previous);
  return choices[Math.floor(random() * choices.length)]!;
}
