import Rings from './Rings'

/** Fixed, decorative page background: layered light, growth rings, film grain. Static by design. */
export default function Backdrop() {
  return (
    <div className="backdrop" aria-hidden>
      <Rings className="bg-rings bg-rings-a" seed={11} count={26} />
      <Rings className="bg-rings bg-rings-b" seed={4} count={14} detail={false} />
      <div className="grain" />
      <div className="vignette" />
    </div>
  )
}
