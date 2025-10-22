import { ReactNode } from 'react';

type ModalProps = {
  open: boolean;
  title?: string;
  onClose: () => void;
  children: ReactNode;
};

export function Modal({ open, title, onClose, children }: ModalProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      {/* Backdrop (no outside-close) */}
      <div className="absolute inset-0 bg-black/40" onClick={(e) => e.preventDefault()} />
      <div className="relative z-10 h-[600px] w-[700px] rounded-xl bg-gray-700 p-6 shadow-xl overflow-y-auto">
        {title && (
          <h2 id="modal-title" className="text-lg font-semibold mb-4">
            {title}
          </h2>
        )}

        {/* Slot for form or any content */}
        {children}
      </div>
    </div>
  );
}
