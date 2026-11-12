import React from 'react';
import {Composition, AbsoluteFill, useCurrentFrame, interpolate, Sequence, spring, useVideoConfig} from 'remotion';
const font = '"Noto Sans KR", sans-serif';
const Typed: React.FC<{text: string; start: number}> = ({text, start}) => {
  const f = useCurrentFrame();
  const n = Math.max(0, Math.min(text.length, Math.round((f - start) * 0.9)));
  return <div style={{whiteSpace: 'pre-wrap', fontSize: 42, lineHeight: 1.5, background: '#2b2f3b', borderRadius: 28, padding: '30px 36px', margin: 34, minHeight: 120}}>{text.slice(0, n)}{n < text.length ? '▍' : ''}</div>;
};
const Step: React.FC<{no: number; title: string; prompt: string; a: string[]; note: string}> = ({no, title, prompt, a, note}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <AbsoluteFill>
    <div style={{position: 'absolute', top: 330, left: 70, fontSize: 64, fontWeight: 900}}><span style={{display: 'inline-block', width: 86, height: 86, lineHeight: '86px', textAlign: 'center', borderRadius: 22, background: '#7c5cff', marginRight: 22}}>{no}</span>{title}</div>
    <div style={{position: 'absolute', top: 470, left: 60, right: 60, height: 700, borderRadius: 40, background: '#171a22', border: '2px solid #2d3240'}}>
      <div style={{height: 78, borderBottom: '2px solid #2d3240', fontSize: 30, color: '#8b93a3', padding: '20px 40px', fontWeight: 700}}>AI 채팅</div>
      <Typed text={prompt} start={8} />
      {a.map((t, i) => <div key={i} style={{margin: '10px 34px', fontSize: 40, opacity: interpolate(f, [60 + i * 8, 70 + i * 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}), transform: `translateX(${interpolate(f, [60 + i * 8, 70 + i * 8], [-30, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}px)`}}>• {t}</div>)}
    </div>
    <div style={{position: 'absolute', top: 1210, left: 70, fontSize: 44, fontWeight: 700, color: '#ffd35c', opacity: spring({frame: f - 75, fps})}}>{note}</div>
  </AbsoluteFill>;
};
const Main: React.FC = () => {
  const f = useCurrentFrame();
  return <AbsoluteFill style={{background: '#0d0f14', color: '#fff', fontFamily: font}}>
    <div style={{position: 'absolute', top: 200, left: 70, right: 70, height: 10, borderRadius: 5, background: '#262a35'}}><div style={{height: '100%', width: `${(f / 600) * 100}%`, background: '#7c5cff', borderRadius: 5}} /></div>
    <div style={{position: 'absolute', top: 240, left: 70, fontSize: 36, fontWeight: 700, color: '#9aa3b2'}}>AI로 생활비 줄이기 · 1편</div>
    <Sequence from={0} durationInFrames={78}><div style={{position: 'absolute', top: 470, left: 70, right: 70, fontSize: 104, fontWeight: 900, lineHeight: 1.18}}>구독료 정리,<br /><span style={{background: '#ffd35c', color: '#0d0f14', padding: '0 16px', borderRadius: 14}}>프롬프트 3줄</span>이면 끝</div></Sequence>
    <Sequence from={78} durationInFrames={150}><Step no={1} title="반복 결제만 뽑기" prompt={'카드 명세서 붙일게.\n매달 반복 결제되는 것만\n표로 정리해 줘.'} a={['넷플릭스 · 유튜브 · 클라우드 · 음악 앱', '매달 반복 결제 목록 정리']} note="준비물: 카드 앱 명세서 복사" /></Sequence>
    <Sequence from={228} durationInFrames={150}><Step no={2} title="겹치는 것 찾기" prompt={'기능이 겹치는 서비스를 묶고,\n하나만 남긴다면 뭘지\n이유와 함께 알려 줘.'} a={['영상 2개 · 저장공간 2개', '하나만 남길 항목과 이유']} note="가족 공유 중인 건 따로 표시" /></Sequence>
    <Sequence from={378} durationInFrames={150}><Step no={3} title="해지 순서 받기" prompt={'해지할 항목을 결제일 순으로\n정렬하고 해지 메뉴 위치를\n단계별로 알려 줘.'} a={['결제일 가까운 것부터', '앱별 해지 메뉴 경로']} note="연간 결제는 환불 조건 먼저 확인" /></Sequence>
    <Sequence from={528} durationInFrames={72}><div style={{position: 'absolute', top: 640, left: 70, right: 70, textAlign: 'center', fontSize: 96, fontWeight: 900, lineHeight: 1.25}}>프롬프트 전문은<br />캡션에<div style={{marginTop: 40, fontSize: 46, color: '#9aa3b2'}}>저장해 두고 월말에 한 번</div></div></Sequence>
  </AbsoluteFill>;
};
export const Root: React.FC = () => <Composition id="Main" component={Main} durationInFrames={600} fps={30} width={1080} height={1920} />;
