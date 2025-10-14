"use client";

import PolicyEditor from "@/components/PolicyEditor";

export default function PolicyPage() {
  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-3">Policy</h1>
      <PolicyEditor />
    </div>
  );
}
