export const metadata = {
  title: "Imprint",
  description: "Company legal imprint.",
};

export default function ImprintPage() {
  return (
    <div className="container mx-auto py-8 prose prose-invert">
      <h1>Imprint</h1>
      <p>
        Provide your company’s legal details here (registered address,
        registration number, VAT ID, and contact details) as required by your
        jurisdiction.
      </p>
    </div>
  );
}
