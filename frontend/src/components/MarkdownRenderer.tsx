"use client";

import React from "react";

interface MarkdownRendererProps {
  content: string;
  onCiteClick?: (citationId: number) => void;
}

/**
 * Clean, zero-dependency Markdown renderer tailored for grounded answers:
 * headings, bullet lists, tables, bold/italic/code, and inline [n] citations.
 */
export function MarkdownRenderer({ content, onCiteClick }: MarkdownRendererProps) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();

    if (!line) {
      i++;
      continue;
    }

    // Tables
    if (line.startsWith("|") && line.endsWith("|")) {
      const tableLines: string[] = [];
      while (
        i < lines.length &&
        lines[i].trim().startsWith("|") &&
        lines[i].trim().endsWith("|")
      ) {
        tableLines.push(lines[i].trim());
        i++;
      }
      if (tableLines.length >= 2) {
        const parseRow = (s: string) =>
          s.slice(1, -1).split("|").map((c) => c.trim());
        const headers = parseRow(tableLines[0]);
        const sep = /^[\s|:-]+$/.test(tableLines[1]);
        const body = tableLines.slice(sep ? 2 : 1).map(parseRow);

        elements.push(
          <div
            key={`t-${i}`}
            className="my-4 overflow-x-auto rounded-lg border border-line bg-surface/60"
          >
            <table className="w-full border-collapse text-left text-[13px]">
              <thead>
                <tr className="border-b border-line bg-accent-soft text-[11px] font-semibold uppercase tracking-wider text-ink-faint">
                  {headers.map((h, hi) => (
                    <th key={hi} className="px-3.5 py-2.5">
                      {formatInline(h, onCiteClick)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-line text-ink-soft">
                {body.map((row, ri) => (
                  <tr key={ri} className="hover:bg-accent-soft/50">
                    {row.map((cell, ci) => (
                      <td
                        key={ci}
                        className={`px-3.5 py-2.5 leading-relaxed ${
                          ci === 0 ? "font-medium text-ink" : ""
                        }`}
                      >
                        {formatInline(cell, onCiteClick)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // Headings
    if (line.startsWith("### ")) {
      elements.push(
        <h4 key={`h4-${i}`} className="mt-4 mb-1.5 text-xs font-semibold uppercase tracking-wider text-accent">
          {formatInline(line.replace("### ", ""), onCiteClick)}
        </h4>
      );
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h3 key={`h3-${i}`} className="mt-4 mb-2 text-sm font-semibold text-ink">
          {formatInline(line.replace("## ", ""), onCiteClick)}
        </h3>
      );
      i++;
      continue;
    }

    // Bullet lists
    if (line.startsWith("- ") || line.startsWith("* ")) {
      const items: string[] = [];
      while (
        i < lines.length &&
        (lines[i].trim().startsWith("- ") || lines[i].trim().startsWith("* "))
      ) {
        items.push(lines[i].trim().slice(2));
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} className="my-2 space-y-1.5 pl-4 text-[13.5px] leading-relaxed text-ink-soft list-disc marker:text-ink-faint">
          {items.map((item, idx) => (
            <li key={idx}>{formatInline(item, onCiteClick)}</li>
          ))}
        </ul>
      );
      continue;
    }

    // Numbered list
    if (/^\d+\.\s/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s/, ""));
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} className="my-2 space-y-1.5 pl-4 text-[13.5px] leading-relaxed text-ink-soft list-decimal marker:text-ink-faint">
          {items.map((item, idx) => (
            <li key={idx}>{formatInline(item, onCiteClick)}</li>
          ))}
        </ol>
      );
      continue;
    }

    // Paragraph
    elements.push(
      <p key={`p-${i}`} className="my-2 text-[13.5px] leading-relaxed text-ink first:mt-0 last:mb-0">
        {formatInline(line, onCiteClick)}
      </p>
    );
    i++;
  }

  return <div className="space-y-2">{elements}</div>;
}

function formatInline(
  text: string,
  onCiteClick?: (id: number) => void
): React.ReactNode[] {
  const tokenRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[\d+\])/g;
  const parts = text.split(tokenRegex);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-ink">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return (
        <em key={index} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={index} className="rounded border border-line bg-accent-soft px-1.5 py-0.5 font-mono text-[11.5px] text-ink">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (/^\[\d+\]$/.test(part)) {
      const id = Number(part.slice(1, -1));
      return (
        <button
          key={index}
          type="button"
          onClick={() => onCiteClick?.(id)}
          className="mx-0.5 inline-flex h-4 items-center justify-center rounded bg-gradient-to-r from-accent to-accent-strong px-1 font-mono text-[10px] font-semibold text-white transition hover:opacity-90"
          aria-label={`Citation ${id}`}
        >
          {id}
        </button>
      );
    }
    return <React.Fragment key={index}>{part}</React.Fragment>;
  });
}
