import { RenderOptions, render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { ReactElement, ReactNode } from "react";
import messages from "../messages/nb.json";

// Test wrapper component that provides i18n context
function TestWrapper({ children }: { children: ReactNode }) {
	return (
		<NextIntlClientProvider locale="nb" messages={messages}>
			{children}
		</NextIntlClientProvider>
	);
}

// Custom render function that includes the i18n wrapper
function customRender(
	ui: ReactElement,
	options?: Omit<RenderOptions, "wrapper">,
) {
	return render(ui, { wrapper: TestWrapper, ...options });
}

// Re-export everything from testing-library
export * from "@testing-library/react";

// Override render with our custom wrapper
export { customRender as render };
