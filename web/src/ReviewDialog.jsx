// 「処理確認」のポップアップ。秘書がこのメールをどう扱ったかを表示する

const THRESHOLD = 0.5;
const ACTIONS = {
  save_reply_draft: "返信の下書きを保存",
  add_event: "予定を登録",
  add_task: "タスクを登録",
  archive_email: "アーカイブ",
};
const STATUS = {
  as_is: "そのまま渡した",
  masked: "伏せ字にして渡した",
  withheld: "丸ごと伏せた（AIには渡していない）",
};

// しきい値以上だった種類と確率
const hits = (scores) =>
  Object.entries(scores ?? {})
    .filter(([, p]) => p >= THRESHOLD)
    .map(([name, p]) => `${name} ${p.toFixed(2)}`);

// 判定と伏せ字の記録（trace）を、判定した単位ごとにまとめる
function toUnits(trace) {
  const units = [];
  for (const step of trace) {
    const last = units[units.length - 1];
    if (step.step === "mask") last.masked = step.text;
    else if (last?.masked !== undefined && !last.recheck) last.recheck = step.scores;
    else units.push({ text: step.text, scores: step.scores });
  }
  return units;
}

function describe(action) {
  const input = action.input;
  if (action.tool === "add_event") return `${input.title}（${input.start} 〜 ${input.end}）`;
  if (action.tool === "add_task") return `${input.title}（期限 ${input.due}）`;
  if (action.tool === "save_reply_draft") return input.body;
  return "";
}

export default function ReviewDialog({ email, features, onClose }) {
  const history = email.history ?? { actions: [] };
  return (
    <div className="overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <button className="close" onClick={onClose}>閉じる</button>
        <h2>処理確認: {email.subject}</h2>

        {history.status && (
          <p className={`status ${history.status}`}>
            {history.guard ? "個人情報をケアしたAI秘書" : "AI秘書"}：{STATUS[history.status]}
          </p>
        )}

        <h3>秘書がしたこと</h3>
        {history.actions.length ? (
          <ul className="actions">
            {history.actions.map((action, i) => (
              <li key={i}>
                <strong>{ACTIONS[action.tool] ?? action.tool}</strong>
                <pre>{describe(action)}</pre>
              </li>
            ))}
          </ul>
        ) : (
          <p className="hint">このメールについて、秘書は何もしませんでした。</p>
        )}

        {features.includes("guard") && history.trace?.length > 0 && (
          <>
            <h3>判定と伏せ字</h3>
            {toUnits(history.trace).map((unit, i) => {
              const found = hits(unit.scores);
              const left = hits(unit.recheck);
              return (
                <div key={i} className={`unit ${found.length ? "found" : ""} ${left.length ? "left" : ""}`}>
                  <div className="text">{unit.text}</div>
                  {found.length > 0 && <div className="tags">検出: {found.join(", ")}</div>}
                  {unit.masked !== undefined && <div className="masked">→ {unit.masked}</div>}
                  {left.length > 0 && <div className="tags">伏せ字にしたあとも検出: {left.join(", ")}</div>}
                </div>
              );
            })}
          </>
        )}

        {features.includes("sent") && history.sent !== undefined && (
          <>
            <h3>AIに渡した内容</h3>
            <pre className="sent">{history.sent}</pre>
          </>
        )}
      </div>
    </div>
  );
}
