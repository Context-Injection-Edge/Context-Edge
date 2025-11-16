
import AdminNav from '@/components/AdminNav';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <AdminNav />
      <main className="p-8">{children}</main>
    </div>
  );
}
