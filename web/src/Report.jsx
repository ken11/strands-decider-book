// 秘書からの報告（Markdown）のうち、見出し・箇条書き・太字だけを表示する

// "**太字**" を <strong> にする
function inline(text) {
  return text.split(/(\*\*[^*]+\*\*)/).map((part, i) =>
    part.startsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : part
  );
}

export default function Report({ text }) {
  return (
    <div className="report">
      {text.split("\n").map((line, i) => {
        if (/^#+\s/.test(line)) return <h4 key={i}>{inline(line.replace(/^#+\s/, ""))}</h4>;
        if (/^\s*[-*]\s/.test(line)) {
          const depth = line.search(/\S/) / 2;
          return (
            <div key={i} className="item" style={{ marginLeft: `${depth + 1}em` }}>
              ・{inline(line.replace(/^\s*[-*]\s/, ""))}
            </div>
          );
        }
        return line.trim() ? <p key={i}>{inline(line)}</p> : null;
      })}
    </div>
  );
}
