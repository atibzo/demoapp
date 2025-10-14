
'use client';
import { useEffect, useState } from 'react';
import { API, j } from '@/lib/api';
export default function AuthRedirectPage(){
  const [s,setS]=useState<'loading'|'ok'|'error'>('loading');
  useEffect(()=>{(async()=>{try{const r=await fetch(`${API}/api/session`); const x=await j(r); setS(x.zerodha?'ok':'error'); setTimeout(()=>location.href='/',800);}catch{setS('error')}})()},[]);
  return <div style={{padding:24}}>{s==='loading'?'Checking session…':s==='ok'?'Login successful':'Login failed'}</div>;
}
