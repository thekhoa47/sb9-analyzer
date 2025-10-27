'use client';
import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/button';
import { configs } from '@/configs/configs';

export default function LoginPageInner() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const next = searchParams.get('next') || '/admin';

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    const r = await fetch(`${configs.NEXT_PUBLIC_BACKEND_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });
    if (r.ok) router.push(next);
    else setErr('Invalid username or password');
  }

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <form onSubmit={onSubmit} className="w-full max-w-sm p-6 border rounded-xl">
        <h1 className="text-xl font-semibold mb-4">Admin Login</h1>
        <input
          className="w-full border rounded p-2 mb-3"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
        <input
          className="w-full border rounded p-2 mb-3"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
        {err && <p className="text-red-600 text-sm mb-3">{err}</p>}
        <Button type="submit">Sign in</Button>
      </form>
    </div>
  );
}
