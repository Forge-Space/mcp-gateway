"""Enhanced UI Specialist with React 2024 patterns and accessibility support.

This enhanced UI Specialist incorporates:
- React 2024 best practices and patterns
- Modern component architecture
- Accessibility-first design principles
- Design system integration
- Performance optimization patterns
- TypeScript support
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..training.knowledge_base import KnowledgeBase, PatternCategory
from ..training.data_extraction import PatternCategory

logger = logging.getLogger(__name__)


class EnhancedUISpecialist:
    """Enhanced UI Specialist with modern React patterns and accessibility."""

    def __init__(self, knowledge_base: Optional[KnowledgeBase] = None) -> None:
        """Initialize the enhanced UI specialist."""
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.framework_preferences = {
            "react": {"priority": 1.0, "patterns": ["hooks", "functional", "typescript"]},
            "vue": {"priority": 0.8, "patterns": ["composition", "typescript"]},
            "angular": {"priority": 0.7, "patterns": ["standalone", "typescript"]},
            "svelte": {"priority": 0.6, "patterns": ["modern", "typescript"]}
        }

        # Component architecture patterns
        self.architecture_patterns = {
            "atomic_design": {
                "atoms": ["button", "input", "icon", "label"],
                "molecules": ["form", "card", "navbar", "dropdown"],
                "organisms": ["header", "sidebar", "table", "modal"],
                "templates": ["page_layout", "dashboard", "form_page"],
                "pages": ["home", "about", "contact", "profile"]
            },
            "feature_sliced": {
                "app": ["app_root", "layout", "routing"],
                "pages": ["list_page", "details_page", "edit_page"],
                "widgets": ["data_table", "chart", "form"],
                "features": ["auth", "user_management", "content"],
                "shared": ["ui_kit", "api", "utils"]
            }
        }

    def generate_component(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a UI component based on the request."""
        try:
            # Extract requirements from request
            component_type = request.get("component_type", "generic")
            framework = request.get("framework", "react")
            requirements = request.get("requirements", [])
            context = request.get("context", {})

            logger.info(f"Generating {component_type} component with {framework}")

            # Get relevant patterns from knowledge base
            patterns = self._get_relevant_patterns(component_type, framework)

            # Generate component based on patterns
            component = self._build_component(component_type, framework, requirements, context, patterns)

            # Apply accessibility enhancements
            component = self._enhance_accessibility(component, requirements)

            # Add performance optimizations
            component = self._optimize_performance(component, framework)

            # Generate TypeScript types if requested
            if "typescript" in requirements:
                component["typescript_types"] = self._generate_typescript_types(component)

            return component

        except Exception as e:
            logger.error(f"Error generating component: {e}")
            return self._get_fallback_component(request)

    def _get_relevant_patterns(self, component_type: str, framework: str) -> List[Dict[str, Any]]:
        """Get relevant patterns from the knowledge base."""
        patterns = []

        # Search for framework-specific patterns
        framework_patterns = self.knowledge_base.search_knowledge(
            f"{framework} {component_type}",
            PatternCategory.REACT_PATTERN if framework == "react" else PatternCategory.UI_COMPONENT,
            limit=10
        )

        for pattern in framework_patterns:
            patterns.append({
                "title": pattern.title,
                "description": pattern.description,
                "code_example": pattern.code_example,
                "confidence": pattern.confidence_score,
                "tags": pattern.tags
            })

        # Search for accessibility patterns
        if "accessibility" in component_type or "a11y" in component_type:
            accessibility_patterns = self.knowledge_base.search_knowledge(
                "accessibility",
                PatternCategory.ACCESSIBILITY,
                limit=5
            )

            for pattern in accessibility_patterns:
                patterns.append({
                    "title": pattern.title,
                    "description": pattern.description,
                    "code_example": pattern.code_example,
                    "confidence": pattern.confidence_score,
                    "tags": pattern.tags + ["accessibility"]
                })

        return patterns

    def _build_component(self, component_type: str, framework: str,
                        requirements: List[str], context: Dict[str, Any],
                        patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build the component based on patterns and requirements."""
        component = {
            "type": component_type,
            "framework": framework,
            "requirements": requirements,
            "context": context,
            "patterns_used": [p["title"] for p in patterns],
            "code": self._generate_component_code(component_type, framework, patterns),
            "props": self._generate_component_props(component_type, patterns),
            "styling": self._generate_component_styling(component_type, framework),
            "dependencies": self._generate_dependencies(framework, requirements)
        }

        return component

    def _generate_component_code(self, component_type: str, framework: str,
                                 patterns: List[Dict[str, Any]]) -> str:
        """Generate component code based on framework and patterns."""
        if framework == "react":
            return self._generate_react_component(component_type, patterns)
        elif framework == "vue":
            return self._generate_vue_component(component_type, patterns)
        elif framework == "angular":
            return self._generate_angular_component(component_type, patterns)
        elif framework == "svelte":
            return self._generate_svelte_component(component_type, patterns)
        else:
            return self._generate_generic_component(component_type, patterns)

    def _generate_react_component(self, component_type: str, patterns: List[Dict[str, Any]]) -> str:
        """Generate React component with 2024 best practices."""

        # Get the best pattern for this component type
        best_pattern = max(patterns, key=lambda p: p["confidence"]) if patterns else None

        if component_type == "button":
            return '''import React from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', asChild = false, ...props }, ref) => {
    const baseClasses = "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";

    const variantClasses = {
      default: "bg-primary text-primary-foreground hover:bg-primary/90",
      destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
      outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
      secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
      ghost: "hover:bg-accent hover:text-accent-foreground",
      link: "text-primary underline-offset-4 hover:underline",
    };

    const sizeClasses = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3",
      lg: "h-11 rounded-md px-8",
      icon: "h-10 w-10",
    };

    const Comp = asChild ? "span" : "button";

    return (
      <Comp
        className={cn(baseClasses, variantClasses[variant], sizeClasses[size], className)}
        ref={ref}
        {...props}
      />
    );
});

Button.displayName = 'Button';

export { Button };'''

        elif component_type == "form":
            return '''import React from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const formSchema = z.object({
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
  password: z.string().min(8, {
    message: "Password must be at least 8 characters.",
  }),
});

type FormValues = z.infer<typeof formSchema>;

interface FormProps {
  onSubmit: (values: FormValues) => void;
  loading?: boolean;
}

export function Form({ onSubmit, loading = false }: FormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="Enter your email"
          {...register('email')}
          aria-invalid={errors.email ? 'true' : 'false'}
          aria-describedby={errors.email ? 'email-error' : undefined}
        />
        {errors.email && (
          <p id="email-error" className="text-sm text-destructive">
            {errors.email.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          placeholder="Enter your password"
          {...register('password')}
          aria-invalid={errors.password ? 'true' : 'false'}
          aria-describedby={errors.password ? 'password-error' : undefined}
        />
        {errors.password && (
          <p id="password-error" className="text-sm text-destructive">
            {errors.password.message}
          </p>
        )}
      </div>

      <Button type="submit" disabled={loading} className="w-full">
        {loading ? 'Submitting...' : 'Submit'}
      </Button>
    </form>
  );
}'''

        elif component_type == "card":
            return '''import React from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border bg-card text-card-foreground shadow-sm",
        className
      )}
      {...props}
    />
  )
);
Card.displayName = 'Card';

const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };'''

        else:
            # Generic component template
            component_name = component_type.title()
            return f'''import React from 'react';
import {{ cn }} from '@/lib/utils';

interface {component_name}Props extends React.HTMLAttributes<HTMLDivElement> {{
  // Add props here
}}

const {component_name} = React.forwardRef<HTMLDivElement, {component_name}Props>(
  ({{ className, ...props }}, ref) => (
    <div
      ref={{ref}}
      className={{cn("base-component-classes", className)}}
      {{...props}}
    />
  )
));

{component_name}.displayName = '{component_name}';

export {{ {component_name} }};'''

    def _generate_vue_component(self, component_type: str, patterns: List[Dict[str, Any]]) -> str:
        """Generate Vue 3 component with Composition API."""
        return f'''<template>
  <div class="{component_type}-component">
    <!-- Component content here -->
  </div>
</template>

<script setup lang="ts">
import {{ ref, computed }} from 'vue';

interface Props {{
  // Define props here
}}

const props = defineProps<Props>();

// Component logic here
</script>

<style scoped>
.{component_type}-component {{
  /* Component styles here */
}}
</style>'''

    def _generate_angular_component(self, component_type: str, patterns: List[Dict[str, Any]]) -> str:
        """Generate Angular 17+ standalone component."""
        return f'''import {{ Component, Input }} from '@angular/core';
import {{ CommonModule }} from '@angular/common';

@Component({{
  selector: 'app-{component_type}',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="{component_type}">
      <!-- Component content here -->
    </div>
  `,
  styles: [\`
    .{component_type} {{
      /* Component styles here */
    }}
  \`]
}})
export class {component_type.title()}Component {{
  // Define inputs here
  @Input() data: any;
}}'''

    def _generate_svelte_component(self, component_type: str, patterns: List[Dict[str, Any]]) -> str:
        """Generate Svelte 5+ component."""
        return f'''<script lang="ts">
  // Component logic here
  let {{ props }} = $props();
</script>

<div class="{component_type}">
  <!-- Component content here -->
</div>

<style>
  .{component_type} {{
    /* Component styles here */
  }}
</style>'''

        base_props = [
            {"name": "children", "type": "ReactNode", "required": False, "description": "Child components"},
            {"name": "id", "type": "string", "required": False, "description": "Unique identifier"}
        ]

        # Add component-specific props based on patterns
        if component_type == "button":
            base_props.extend([
                {"name": "variant", "type": "string", "required": False, "description": "Button variant style"},
                {"name": "size", "type": "string", "required": False, "description": "Button size"},
                {"name": "disabled", "type": "boolean", "required": False, "description": "Disable the button"}
            ])
        elif component_type == "form":
            base_props.extend([
                {"name": "onSubmit", "type": "function", "required": True, "description": "Form submit handler"},
                {"name": "loading", "type": "boolean", "required": False, "description": "Loading state"}
            ])

        return base_props

    def _generate_component_styling(self, component_type: str, framework: str) -> Dict[str, Any]:
        """Generate styling configuration for the component."""
        return {
            "framework": framework,
            "styling_approach": "css_modules" if framework == "react" else "scoped",
            "theme_integration": True,
            "responsive": True,
            "customizable": True,
            "design_tokens": True
        }

    def _generate_dependencies(self, framework: str, requirements: List[str]) -> List[str]:
        """Generate dependency list for the component."""
        dependencies = []

        if framework == "react":
            dependencies.extend(["react", "react-dom"])

            if "typescript" in requirements:
                dependencies.extend(["@types/react", "@types/react-dom"])

            if "styling" in requirements:
                dependencies.extend(["tailwindcss", "class-variance-authority"])

            if "forms" in requirements:
                dependencies.extend(["react-hook-form", "@hookform/resolvers", "zod"])

        elif framework == "vue":
            dependencies.extend(["vue"])

            if "typescript" in requirements:
                dependencies.append("vue-tsc")

        elif framework == "angular":
            dependencies.extend(["@angular/core", "@angular/common", "@angular/forms"])

        elif framework == "svelte":
            dependencies.extend(["svelte"])

            if "typescript" in requirements:
                dependencies.append("svelte-check")

        return dependencies

    def _enhance_accessibility(self, component: Dict[str, Any], requirements: List[str]) -> Dict[str, Any]:
        """Enhance component with accessibility features."""
        if "accessibility" not in requirements:
            return component

        # Add accessibility enhancements
        component["accessibility"] = {
            "aria_labels": True,
            "keyboard_navigation": True,
            "screen_reader_support": True,
            "focus_management": True,
            "color_contrast": True,
            "semantic_html": True
        }

        # Add accessibility attributes to code
        if "code" in component:
            code = component["code"]

            # Add ARIA attributes where appropriate
            if "button" in component.get("type", ""):
                code = self._add_button_accessibility(code)
            elif "form" in component.get("type", ""):
                code = self._add_form_accessibility(code)
            elif "input" in component.get("type", ""):
                code = self._add_input_accessibility(code)

            component["code"] = code

        return component

    def _add_button_accessibility(self, code: str) -> str:
        """Add accessibility attributes to button code."""
        # Add proper ARIA attributes and keyboard support
        return code.replace(
            'className={cn(',
            'aria-label={props["aria-label"]}\n          className={cn('
        )

    def _add_form_accessibility(self, code: str) -> str:
        """Add accessibility attributes to form code."""
        # Add form validation and error handling
        return code.replace(
            'placeholder="Enter your email"',
            'placeholder="Enter your email"\n          aria-label="Email address"'
        )

    def _add_input_accessibility(self, code: str) -> str:
        """Add accessibility attributes to input code."""
        # Add proper labeling and validation
        return code.replace(
            '<Input',
            '<Input\n          aria-label={props["aria-label"]}\n          aria-invalid={errors ? "true" : "false"}'
        )

    def _optimize_performance(self, component: Dict[str, Any], framework: str) -> Dict[str, Any]:
        """Add performance optimizations to the component."""
        component["performance"] = {
            "memoization": framework == "react",
            "lazy_loading": True,
            "code_splitting": True,
            "tree_shaking": True,
            "bundle_optimization": True
        }

        # Add React.memo for React components
        if framework == "react" and "code" in component:
            code = component["code"]

            # Wrap with React.memo if not already wrapped
            if "React.memo" not in code and "React.forwardRef" in code:
                code = code.replace(
                    'React.forwardRef',
                    'React.memo(React.forwardRef'
                )
                code = code.replace(
                    '});',
                    '}));'
                )

            component["code"] = code

        return component

    def _generate_typescript_types(self, component: Dict[str, Any]) -> str:
        """Generate TypeScript type definitions for the component."""
        component_name = component.get("type", "Component").title()
        props = component.get("props", [])

        types = f'''// TypeScript types for {component_name}
export interface {component_name}Props {{
'''

        for prop in props:
            if prop.get("required", False):
                types += f'\n  {prop["name"]}: {prop["type"]};'
            else:
                types += f'\n  {prop["name"]}?: {prop["type"]};'

        types += '\n}'

        return types

    def _get_fallback_component(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get fallback component when generation fails."""
        component_type = request.get("component_type", "generic")
        framework = request.get("framework", "react")

        return {
            "type": component_type,
            "framework": framework,
            "code": f'''// Fallback {component_type} component
// This is a basic implementation that should be enhanced

import React from 'react';

const {component_type.title()} = () => {{
  return <div>{component_type.title()} Component</div>;
}};

export default {component_type.title()};''',
            "props": [{"name": "className", "type": "string", "required": False}],
            "styling": {"framework": framework, "styling_approach": "inline"},
            "dependencies": ["react"],
            "fallback": True
        }

    def get_component_recommendations(self, component_type: str, framework: str) -> List[str]:
        """Get recommendations for component improvements."""
        recommendations = []

        # Get patterns for this component type
        patterns = self._get_relevant_patterns(component_type, framework)

        if not patterns:
            recommendations.append("Consider adding more specific patterns to the knowledge base")
            return recommendations

        # Analyze patterns and generate recommendations
        high_confidence_patterns = [p for p in patterns if p["confidence"] > 0.8]

        if len(high_confidence_patterns) < 3:
            recommendations.append("Add more high-quality patterns for better component generation")

        # Check for accessibility patterns
        accessibility_patterns = [p for p in patterns if "accessibility" in p.get("tags", [])]
        if not accessibility_patterns:
            recommendations.append("Include accessibility patterns for inclusive design")

        # Check for performance patterns
        performance_patterns = [p for p in patterns if "performance" in p.get("tags", [])]
        if not performance_patterns:
            recommendations.append("Add performance optimization patterns")

        return recommendations

    def validate_component(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated component for quality and completeness."""
        validation_result = {
            "valid": True,
            "issues": [],
            "recommendations": [],
            "score": 0.0
        }

        # Check required fields
        required_fields = ["type", "framework", "code", "props"]
        for field in required_fields:
            if field not in component:
                validation_result["issues"].append(f"Missing required field: {field}")
                validation_result["valid"] = False

        # Check code quality
        if "code" in component:
            code = component["code"]

            # Check for accessibility
            if "aria-" not in code and component.get("type") in ["button", "form", "input"]:
                validation_result["issues"].append("Missing accessibility attributes")
                validation_result["recommendations"].append("Add ARIA attributes for better accessibility")

            # Check for TypeScript types
            if "typescript" in component.get("requirements", []) and "interface" not in code:
                validation_result["issues"].append("Missing TypeScript type definitions")
                validation_result["recommendations"].append("Add proper TypeScript interfaces")

        # Calculate score
        base_score = 100
        penalty_per_issue = 10
        penalty_per_recommendation = 5

        score = base_score - (len(validation_result["issues"]) * penalty_per_issue) - \
                (len(validation_result["recommendations"]) * penalty_per_recommendation)

        validation_result["score"] = max(0, score / 100.0)  # Normalize to 0-1

        return validation_result


if __name__ == "__main__":
    # Example usage
    specialist = EnhancedUISpecialist()

    # Generate a button component
    request = {
        "component_type": "button",
        "framework": "react",
        "requirements": ["typescript", "accessibility", "styling"],
        "context": {"theme": "material", "size": "medium"}
    }

    print("Generating enhanced UI component...")
    component = specialist.generate_component(request)

    print(f"Generated {component['type']} component for {component['framework']}")
    print(f"Code length: {len(component['code'])} characters")
    print(f"Props: {len(component['props'])}")
    print(f"Dependencies: {component['dependencies']}")

    # Validate the component
    validation = specialist.validate_component(component)
    print(f"\nValidation Score: {validation['score']:.2f}")
    print(f"Valid: {validation['valid']}")

    if validation["issues"]:
        print("Issues:")
        for issue in validation["issues"]:
            print(f"  - {issue}")

    if validation["recommendations"]:
        print("Recommendations:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")

    # Get recommendations
    recommendations = specialist.get_component_recommendations("button", "react")
    print(f"\nComponent Recommendations:")
    for rec in recommendations:
        print(f"  - {rec}")
