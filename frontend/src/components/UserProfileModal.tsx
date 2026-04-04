"use client";

import { useState } from "react";
import { updateProfile, changePassword, ApiError } from "@/lib/api";

type Props = {
  username: string;
  displayName: string;
  onClose: () => void;
  onUpdate: (displayName: string) => void;
};

export function UserProfileModal({ username, displayName, onClose, onUpdate }: Props) {
  const [name, setName] = useState(displayName);
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [nameMsg, setNameMsg] = useState("");
  const [pwMsg, setPwMsg] = useState("");
  const [saving, setSaving] = useState(false);

  const handleNameSave = async () => {
    if (!name.trim()) return;
    setSaving(true);
    setNameMsg("");
    try {
      const res = await updateProfile(name.trim());
      onUpdate(res.display_name);
      setNameMsg("Saved");
    } catch (err) {
      setNameMsg(err instanceof ApiError ? "Failed to save" : "Error");
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    if (!currentPw || newPw.length < 4) {
      setPwMsg("New password must be at least 4 characters");
      return;
    }
    setSaving(true);
    setPwMsg("");
    try {
      await changePassword(currentPw, newPw);
      setPwMsg("Password changed");
      setCurrentPw("");
      setNewPw("");
    } catch (err) {
      if (err instanceof ApiError && err.status === 403) {
        setPwMsg("Current password is incorrect");
      } else {
        setPwMsg("Failed to change password");
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-2xl border border-[var(--stroke)] bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="font-display text-xl font-semibold text-[var(--navy-dark)]">Profile</h2>
          <button onClick={onClose} className="text-[var(--gray-text)] hover:text-[var(--navy-dark)]">
            &times;
          </button>
        </div>

        <p className="mt-2 text-xs text-[var(--gray-text)]">Username: {username}</p>

        <div className="mt-5">
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Display name
          </label>
          <div className="flex gap-2">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="flex-1 rounded-lg border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
            />
            <button
              onClick={handleNameSave}
              disabled={saving}
              className="rounded-lg bg-[var(--primary-blue)] px-4 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
            >
              Save
            </button>
          </div>
          {nameMsg && <p className="mt-1 text-xs text-[var(--gray-text)]">{nameMsg}</p>}
        </div>

        <div className="mt-6">
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)]">
            Change password
          </label>
          <input
            type="password"
            placeholder="Current password"
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
            className="mb-2 w-full rounded-lg border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
          <input
            type="password"
            placeholder="New password (min 4 chars)"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            className="mb-2 w-full rounded-lg border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm outline-none focus:border-[var(--primary-blue)]"
          />
          <button
            onClick={handlePasswordChange}
            disabled={saving}
            className="rounded-lg bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
          >
            Change Password
          </button>
          {pwMsg && <p className="mt-1 text-xs text-[var(--gray-text)]">{pwMsg}</p>}
        </div>
      </div>
    </div>
  );
}
