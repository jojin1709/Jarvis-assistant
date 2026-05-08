import logo from "../assets/logo.png";

export default function LogoMark({ className = "h-10 w-10", rounded = "rounded-2xl" }) {
  return (
    <span className={`inline-grid shrink-0 place-items-center overflow-hidden border border-white/10 bg-[#0B1020] shadow-lg shadow-black/20 ${rounded} ${className}`}>
      <img src={logo} alt="JX Jarvis logo" className="h-full w-full object-cover" />
    </span>
  );
}
