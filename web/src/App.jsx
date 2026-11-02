import { useEffect, useState } from "react";
import Report from "./Report.jsx";
import ReviewDialog from "./ReviewDialog.jsx";

const TABS = { inbox: "受信トレイ", archive: "アーカイブ", tasks: "タスク", calendar: "カレンダー" };

// "松本 恵子 <matsumoto@...>" から名前だけを取り出す
const senderName = (from) => from.replace(/\s*<.*>$/, "");
const shortDate = (iso) => iso.slice(5, 16).replace("-", "/").replace("T", " ");
const fullDate = (iso) => iso.slice(0, 16).replaceAll("-", "/").replace("T", " ");

async function api(path, options) {
  const response = await fetch(`/api${path}`, options);
  if (!response.ok) throw new Error((await response.json()).detail ?? response.statusText);
  return response.json();
}

const post = (path, body) =>
  api(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });

export default function App() {
  const [info, setInfo] = useState(null);
  const [tab, setTab] = useState("inbox");
  const [emails, setEmails] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState({ running: false, last_run: null });
  const [checked, setChecked] = useState([]);
  const [opened, setOpened] = useState(null);
  const [review, setReview] = useState(null);

  // 先に状態を確かめてから、メールなどを読み込む（処理が終わった直後の結果を取りこぼさないため）
  async function reload() {
    setStatus(await api("/status"));
    setEmails(await api("/emails"));
    setTasks(await api("/tasks"));
    setEvents(await api("/events"));
  }

  useEffect(() => {
    api("/info").then(setInfo);
    reload();
  }, []);

  // 秘書が処理している間は、2秒ごとに画面を更新する
  useEffect(() => {
    if (!status.running) return;
    const timer = setInterval(reload, 2000);
    return () => clearInterval(timer);
  }, [status.running]);

  async function startSecretary(guard) {
    await post("/secretary", { email_ids: checked, guard });
    setStatus({ ...status, running: true, email_ids: checked });
    setChecked([]);
  }

  async function openEmail(id) {
    await post(`/emails/${id}/read`);
    setOpened(await api(`/emails/${id}`));
    reload();
  }

  async function reset() {
    await post("/reset");
    setChecked([]);
    setOpened(null);
    reload();
  }

  const features = info?.features ?? [];
  const shown = emails.filter((e) => e.archived === (tab === "archive"));
  const allChecked = shown.length > 0 && shown.every((e) => checked.includes(e.id));
  const toggle = (id) =>
    setChecked((prev) => (prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]));

  return (
    <div className="app">
      <header>
        <h1>見本メール</h1>
        <nav>
          {Object.entries(TABS).map(([key, label]) => (
            <button key={key} className={tab === key ? "on" : ""} onClick={() => setTab(key)}>
              {label}
            </button>
          ))}
        </nav>
        <div className="spacer" />
        <button onClick={reset} disabled={status.running}>初期状態に戻す</button>
      </header>

      {(tab === "inbox" || tab === "archive") && (
        <main className="mailbox">
          <div className="toolbar">
            <input type="checkbox" checked={allChecked}
              onChange={() => setChecked(allChecked ? [] : shown.map((e) => e.id))} />
            <button className="primary" disabled={!checked.length || status.running}
              onClick={() => startSecretary(false)}>
              AI秘書に任せる
            </button>
            {features.includes("guard") && (
              <button className="care" disabled={!checked.length || status.running}
                onClick={() => startSecretary(true)}>
                個人情報をケアしたAI秘書に任せる
              </button>
            )}
            {status.running && <span className="running">秘書が処理しています…</span>}
            <span className="count">{checked.length}通を選択中</span>
          </div>

          {status.last_run && !status.running && <LastRun run={status.last_run} />}

          <div className="panes">
            <ul className="list">
              {shown.map((e) => (
                <li key={e.id} className={`${e.read ? "read" : "unread"} ${opened?.id === e.id ? "opened" : ""}`}>
                  <input type="checkbox" checked={checked.includes(e.id)} onChange={() => toggle(e.id)} />
                  <div className="row" onClick={() => openEmail(e.id)}>
                    <span className="from">{senderName(e.from)}</span>
                    <span className="subject">{e.subject}</span>
                    {status.running && status.email_ids.includes(e.id) && (
                      <span className="badge working">AI秘書が対応中</span>
                    )}
                    {e.draft && <span className="badge">下書きあり</span>}
                    <span className="date">{shortDate(e.date)}</span>
                  </div>
                  {e.processed && (
                    <button className="small" onClick={async () => setReview(await api(`/emails/${e.id}`))}>
                      処理確認
                    </button>
                  )}
                </li>
              ))}
            </ul>
            <MailView email={opened} />
          </div>
        </main>
      )}

      {tab === "tasks" && <Tasks tasks={tasks} />}
      {tab === "calendar" && <Calendar events={events} />}
      {review && <ReviewDialog email={review} features={features} onClose={() => setReview(null)} />}
    </div>
  );
}

// 開いたメールの本文と、秘書が作った返信の下書き
function MailView({ email }) {
  if (!email) return <div className="mail empty">メールを選ぶと、ここに本文が表示されます。</div>;
  return (
    <div className="mail">
      <h2>{email.subject}</h2>
      <div className="meta">{email.from}<br />{fullDate(email.date)}</div>
      <pre>{email.body}</pre>
      {email.drafts.map((draft, i) => (
        <div key={i} className="draft">
          <h3>返信の下書き</h3>
          <pre>{draft}</pre>
        </div>
      ))}
    </div>
  );
}

// 直前の実行の結果
function LastRun({ run }) {
  if (run.error) return <div className="last-run error">エラー: {run.error}</div>;
  return (
    <details className="last-run">
      <summary>
        秘書からの報告（{run.seconds}秒、入力 {run.input_tokens.toLocaleString()} / 出力{" "}
        {run.output_tokens.toLocaleString()} トークン）
      </summary>
      <Report text={run.report} />
    </details>
  );
}

function Tasks({ tasks }) {
  return (
    <main className="page">
      <table>
        <thead><tr><th>期限</th><th>タスク</th><th>もとのメール</th></tr></thead>
        <tbody>
          {tasks.map((t, i) => (
            <tr key={i}><td>{t.due}</td><td>{t.title}</td><td>{t.email_id ?? ""}</td></tr>
          ))}
        </tbody>
      </table>
      {!tasks.length && <p className="hint">タスクはまだありません。</p>}
    </main>
  );
}

function Calendar({ events }) {
  return (
    <main className="page">
      <table>
        <thead><tr><th>日時</th><th>予定</th><th>もとのメール</th></tr></thead>
        <tbody>
          {events.map((e, i) => (
            <tr key={i} className={e.email_id ? "added" : ""}>
              <td>{shortDate(e.start)} 〜 {e.end.slice(11, 16)}</td>
              <td>{e.title}</td>
              <td>{e.email_id ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
