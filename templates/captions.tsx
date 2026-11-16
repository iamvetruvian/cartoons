// Hormozi-style popup captions (copy to src/videos/<name>/captions.tsx and render inside the composition).
// Montserrat ExtraBold, ALL CAPS, white with a thick black outline. Each page (5-7 words) pops in as a unit;
// only the yellow highlight travels with the voice. Hard page cuts. Timing comes from the voice's words.json
// (single source of truth with the mix): replace the import below with your own voice/words.json.
// Never more than two lines: pages hold ~1.7 s of speech via createTikTokStyleCaptions (@remotion/captions,
// same version as remotion) and are hard-capped at 6 balanced tokens.
// Prove the cap by measuring EVERY page with the real woff2 over every active-word case, not by eyeballing stills.
// Needs public/fonts/Montserrat-ExtraBold.woff2 (Google Fonts, latin subset).
import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { createTikTokStyleCaptions, TikTokPage } from "@remotion/captions";
import wordsData from "../words.json"; // <-- your voice/words.json: [{w, s, e}]

type Word = { w: string; s: number; e: number };
const WORDS = wordsData as Word[];

const FONT_SIZE = 70;
const ACTIVE = "#FFEA00";
const MAX_TOKENS = 6;

const display = (w: string) => w.trim().replace(/[.,?!]+$/g, "").toUpperCase();

const pages: TikTokPage[] = (() => {
  const captions = WORDS.map((w, i) => ({ text: (i === 0 ? "" : " ") + w.w, startMs: w.s * 1000, endMs: w.e * 1000, timestampMs: null, confidence: null }));
  const { pages } = createTikTokStyleCaptions({ captions, combineTokensWithinMilliseconds: 1700, breakOnSilenceAfterMilliseconds: 350 });
  // hard cap: split any page over MAX_TOKENS so two lines always suffice
  const out: TikTokPage[] = [];
  for (const [pi, p] of pages.entries()) {
    const chunks: typeof p.tokens[] = [];
    const nCh = Math.ceil(p.tokens.length / MAX_TOKENS), size = Math.ceil(p.tokens.length / nCh);
    for (let i = 0; i < p.tokens.length; i += size) chunks.push(p.tokens.slice(i, i + size));
    chunks.forEach((tokens, ci) => {
      const startMs = tokens[0].fromMs;
      const next = ci + 1 < chunks.length ? chunks[ci + 1][0].fromMs : pi + 1 < pages.length ? pages[pi + 1].startMs : p.startMs + p.durationMs;
      out.push({ text: tokens.map((t) => t.text).join(""), startMs, tokens, durationMs: Math.max(1, next - startMs) });
    });
  }
  return out;
})();

const pageAt = (ms: number) => pages.find((p) => ms >= p.startMs && ms < p.startMs + p.durationMs) ?? null;

const WordPop: React.FC<{ text: string; active: boolean }> = ({ text, active }) => (
  <span style={{
    display: "inline-block",
    color: active ? ACTIVE : "#ffffff",
    WebkitTextStroke: `${FONT_SIZE * 0.11}px #000000`,
    paintOrder: "stroke fill",
  }}>
    {text}
  </span>
);

export const Captions: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [handle] = useState(() => delayRender("captions font"));
  useEffect(() => {
    const face = new FontFace("Montserrat", `url(${staticFile("fonts/Montserrat-ExtraBold.woff2")})`, { weight: "800" });
    face.load().then((f) => { document.fonts.add(f); continueRender(handle); })
      .catch((e) => { console.error("caption font failed, falling back", e); continueRender(handle); });
  }, [handle]);
  const ms = (frame / fps) * 1000;
  const page = useMemo(() => pageAt(ms), [ms]);
  const pop = spring({ frame: page ? frame - Math.round((page.startMs / 1000) * fps) : 0, fps, config: { damping: 14, stiffness: 300, mass: 0.5 } });
  if (!page) return null;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 330, pointerEvents: "none" }}>
      <div key={page.startMs} style={{
        display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "baseline",
        maxWidth: 980, columnGap: 36, rowGap: 0,
        fontFamily: "Montserrat, sans-serif", fontWeight: 800, fontSize: FONT_SIZE, lineHeight: 1.08,
        transform: `scale(${0.9 + 0.1 * pop})`,
      }}>
        {page.tokens.map((t, i) => (
          <WordPop key={`${page.startMs}-${i}`} text={display(t.text)} active={ms >= t.fromMs && ms < t.toMs} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
