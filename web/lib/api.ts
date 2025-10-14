export const API = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
export async function j(r:Response){ if(!r.ok) throw r; return r.json(); }
