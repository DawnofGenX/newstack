import Counter from "./counter";

export default function Home() {
  return (
    <main className="flex flex-1 w-full flex-col items-center justify-center gap-8 bg-zinc-50 px-6 py-24 font-sans dark:bg-black">
      <div className="flex w-full max-w-md flex-col gap-4 rounded-2xl bg-white p-8 shadow-sm ring-1 ring-black/[.06] dark:bg-zinc-900 dark:ring-white/[.08]">
        <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
          {{ title }}
        </h1>
        <p className="text-base leading-7 text-zinc-600 dark:text-zinc-400">
          {{ description }}
        </p>
        <Counter />
      </div>
    </main>
  );
}
