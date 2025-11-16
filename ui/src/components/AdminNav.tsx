'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function AdminNav() {
  const pathname = usePathname();
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  // Check Edge Server connection
  useEffect(() => {
    const checkServer = async () => {
      try {
        const response = await fetch('http://localhost:5000/health', {
          method: 'GET',
          signal: AbortSignal.timeout(2000)
        });
        setServerStatus(response.ok ? 'online' : 'offline');
      } catch (error) {
        setServerStatus('offline');
      }
    };

    checkServer();
    const interval = setInterval(checkServer, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { href: '/admin/devices', label: 'Devices', icon: '🏭' },
    { href: '/admin/devices/setup-wizard', label: 'Add Device', icon: '➕' },
    { href: '/admin/health', label: 'Health Monitor', icon: '🚦' },
    { href: '/admin/recommendations', label: 'Recommendations', icon: '💡' },
  ];

  return (
    <nav className="bg-gradient-to-r from-blue-900 to-blue-700 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/admin/devices" className="flex items-center gap-3 group">
            <div className="text-3xl group-hover:scale-110 transition-transform">⚡</div>
            <div>
              <div className="text-xl font-bold">Context Edge</div>
              <div className="text-xs opacity-75">Industrial AI Platform</div>
            </div>
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
                    ${isActive
                      ? 'bg-white text-blue-900 shadow-lg'
                      : 'text-white hover:bg-blue-800'
                    }
                  `}
                >
                  <span className="text-lg">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* Server Status */}
          <div className={`
            flex items-center gap-2 px-4 py-2 rounded-lg font-medium border-2
            ${serverStatus === 'online'
              ? 'bg-green-500/20 border-green-400 text-green-100'
              : serverStatus === 'offline'
              ? 'bg-red-500/20 border-red-400 text-red-100'
              : 'bg-gray-500/20 border-gray-400 text-gray-100'
            }
          `}>
            <div className={`
              w-3 h-3 rounded-full
              ${serverStatus === 'online'
                ? 'bg-green-400 animate-pulse'
                : serverStatus === 'offline'
                ? 'bg-red-400'
                : 'bg-gray-400 animate-pulse'
              }
            `} />
            <span className="text-sm">
              {serverStatus === 'online' && '🟢 Edge Server Online'}
              {serverStatus === 'offline' && '🔴 Edge Server Offline'}
              {serverStatus === 'checking' && '⚪ Checking...'}
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
}
