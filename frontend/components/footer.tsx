import Image from "next/image";

export function Footer() {
  return (
    <footer className="border-t mt-auto py-4">
      <div className="container mx-auto px-8 flex items-center justify-center gap-2 text-sm text-muted-foreground">
        <span>Built by</span>
        <Image
          src="/panthra-logo-light.svg"
          alt="Panthra"
          width={80}
          height={20}
          className="dark:invert opacity-70 hover:opacity-100 transition-opacity"
        />
      </div>
    </footer>
  );
}
