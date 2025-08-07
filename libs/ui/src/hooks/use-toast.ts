import { toast as sonnerToast, Toaster } from "sonner";

/**
 * Basic toast hook using sonner.
 */
export function useToast() {
  /**
   * Show a toast.
   * @param message The message to display.
   * @param options Optional toast options.
   */
  function toast(
    message: string,
    options?: {
      id?: string;
      duration?: number;
      position?:
        | "top-left"
        | "top-center"
        | "top-right"
        | "bottom-left"
        | "bottom-center"
        | "bottom-right";
      variant?: "default" | "success" | "error" | "warning" | "info";
    },
  ) {
    // 'variant' is not a valid property for sonner's toast options as of latest versions.
    // If you want to style based on variant, you should use the 'className' or 'description' props, or use custom logic.
    // Here, we just pass the supported options.
    return sonnerToast(message, {
      id: options?.id,
      duration: options?.duration,
      position: options?.position,
    });
  }

  /**
   * Dismiss toast message(s) with optional id as argument.
   * if id is not provided, all toasts will be dismissed.
   * @param id The id of the toast to dismiss.
   */
  function dismiss(id?: string) {
    sonnerToast.dismiss(id);
  }

  /**
   * Dismiss all toasts.
   */
  function dismissAll() {
    sonnerToast.dismiss();
  }

  return {
    toast,
    dismiss,
    dismissAll,
    Toaster,
  };
}
