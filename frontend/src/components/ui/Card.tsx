type CardProps = {
  children: React.ReactNode;
};

export default function Card({ children }: CardProps) {
  return (
    <div className="rounded-lg border p-4 shadow bg-white">
      {children}
    </div>
  );
}