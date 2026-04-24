import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { Toast, type ToastType } from '../components/Toast';

type ToastState = {
  id: number;
  text: string;
  type: ToastType;
};

type ToastContextValue = {
  toast: ToastState | null;
  showToast: (text: string, type: ToastType) => void;
  hideToast: () => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null);

  const hideToast = useCallback(() => {
    setToast(null);
  }, []);

  const showToast = useCallback((text: string, type: ToastType) => {
    setToast({
      id: Date.now(),
      text,
      type,
    });
  }, []);

  const value = useMemo(
    () => ({
      toast,
      showToast,
      hideToast,
    }),
    [hideToast, showToast, toast],
  );

  return createElement(ToastContext.Provider, { value }, children);
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used inside ToastProvider');
  }
  return {
    showToast: context.showToast,
    hideToast: context.hideToast,
  };
}

export function ToastContainer() {
  const context = useContext(ToastContext);
  if (!context || !context.toast) {
    return null;
  }

  return createElement(Toast, {
    key: context.toast.id,
    text: context.toast.text,
    type: context.toast.type,
    onClose: context.hideToast,
  });
}
