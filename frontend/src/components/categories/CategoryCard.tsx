"use client";

import { Button } from "@/components/ui/button";
import { Edit, Trash2, Users, Eye } from "lucide-react";
import type { Category } from "@/types/category";

// Dégradés prédéfinis pour les catégories
const GRADIENTS = [
  "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  "linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%)",
  "linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)",
  "linear-gradient(135deg, #2c3e50 0%, #3498db 100%)",
  "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
];

function getGradient(id: number): string {
  return GRADIENTS[id % GRADIENTS.length];
}

interface CategoryCardProps {
  category: Category;
  onEdit?: (category: Category) => void;
  onDelete?: (category: Category) => void;
  onView?: (category: Category) => void;
}

export function CategoryCard({
  category,
  onEdit,
  onDelete,
  onView,
}: CategoryCardProps) {
  const gradient = getGradient(category.id);
  const contactsCount = category.contact_count ?? 0;

  return (
    <div className="rounded-2xl bg-white shadow-card overflow-hidden hover:shadow-card-hover transition-shadow border border-[#E5E7EB]/50">
      {/* En-tête avec gradient */}
      <div
        className="p-5 text-white"
        style={{ background: gradient }}
      >
        <h3 className="text-lg font-semibold truncate">{category.name}</h3>
        <div className="flex items-center gap-2 mt-2 text-white/90">
          <Users className="h-4 w-4" />
          <span className="text-sm">
            {contactsCount} contact{contactsCount !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Contenu */}
      <div className="p-4">
        <p className="text-xs text-[#6B7280]">
          Créée le {new Date(category.created_at).toLocaleDateString("fr-FR")}
        </p>
        
        {/* Actions */}
        <div className="flex gap-2 mt-4">
          {onView && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onView(category)}
              className="flex-1 min-h-[40px] touch-manipulation"
            >
              <Eye className="h-4 w-4 mr-2" />
              Voir
            </Button>
          )}
          {onEdit && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onEdit(category)}
              className="min-h-[40px] min-w-[40px] touch-manipulation text-[#6B7280] hover:text-[#111827]"
            >
              <Edit className="h-4 w-4" />
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(category)}
              className="min-h-[40px] min-w-[40px] touch-manipulation text-[#6B7280] hover:text-[#EF4444] hover:bg-[#FEE2E2]"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export default CategoryCard;
