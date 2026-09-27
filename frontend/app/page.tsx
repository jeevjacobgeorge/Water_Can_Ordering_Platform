export default function HomePage() {
  return (
    <main className="min-h-screen bg-sky-50 px-5 py-8 text-slate-900">
      <section className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-md flex-col justify-between rounded-3xl bg-white p-6 shadow-sm ring-1 ring-sky-100">
        <div>
          <div className="mb-10 flex h-12 w-12 items-center justify-center rounded-2xl bg-water-600 text-2xl text-white">
            💧
          </div>
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-water-700">
            Water Can Delivery
          </p>
          <h1 className="text-4xl font-bold leading-tight">
            Fresh water delivered to your door.
          </h1>
          <p className="mt-4 text-base leading-7 text-slate-600">
            Enter your phone number to start a new order or quickly refill your
            usual cans.
          </p>
        </div>

        <div className="space-y-4">
          <label className="block text-sm font-semibold" htmlFor="phone">
            Phone number
          </label>
          <input
            className="h-14 w-full rounded-2xl border border-slate-200 px-4 text-lg outline-none transition focus:border-water-600 focus:ring-4 focus:ring-sky-100"
            id="phone"
            inputMode="numeric"
            placeholder="9876543210"
            type="tel"
          />
          <button className="h-14 w-full rounded-2xl bg-water-600 px-5 text-base font-bold text-white transition hover:bg-water-700">
            Continue
          </button>
          <p className="text-center text-xs text-slate-500">
            No account or password required.
          </p>
        </div>
      </section>
    </main>
  );
}
