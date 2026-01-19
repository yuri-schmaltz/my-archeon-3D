import { forwardRef } from "react";
import { cn } from "../../lib/utils";

interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {
    min: number;
    max: number;
    step?: number;
}

const Slider = forwardRef<HTMLInputElement, SliderProps>(
    ({ className, min, max, step, value, onChange, ...props }, ref) => {
        return (
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={onChange}
                className={cn(
                    "w-full h-2 bg-secondary rounded-lg appearance-none cursor-pointer accent-primary",
                    className
                )}
                ref={ref}
                {...props}
            />
        );
    }
);
Slider.displayName = "Slider";

export { Slider };
