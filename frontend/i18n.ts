import { getRequestConfig } from "next-intl/server";

export default getRequestConfig(async () => {
	// For now, we only support Norwegian
	const locale = "nb";

	return {
		locale,
		messages: (await import(`./messages/${locale}.json`)).default,
	};
});
