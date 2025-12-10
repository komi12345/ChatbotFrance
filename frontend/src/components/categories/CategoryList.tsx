"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { CategoryCard } from "./CategoryCard";
import { Search, Plus, Loader2 } from "lucide-react";
import type { Category } from "@/types/category";

interface CategoryListProps {
  categories: Category[];
  isLoading?: boolean;
  onCreate?: () => void;
  onEdit?: (category: Category) => void;
  onDelete?: (category: Category) => void;
  onView?: (category: Category) => void;
  onSearch?: (search: string) => void;
  initialSearch?: string;
}

export function CategoryList({
  categories,
  isLoading = false,
  onCreate,
  onEdit,
  onDelete,
  onView,
  onSearch,
  initialSearch = "",
}: CategoryListProps) {
  const [searchValue, setSearchValue] = useState(initialSearch);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch?.(searchValue);
  };

  return (
    <div className="space-y-6">
      {/* Barre de recherche et bouton créer */}
      <div className="flex flex-col sm:flex-row gap-4">
        <form
          onSubmit={handleSearchSubmit}
          className="flex-1 flex gap-2"
        >
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#9CA3AF]" />
            <Input
              placeholder="Rechercher une catégorie..."
              value={searchValue}
              onChange={handleSearchChange}
              className="pl-10"
            />
          </div>
          <Button type="submit" variant="secondary">
            Rechercher
          </Button>
        </form>

        {onCreate && (
          <Button onClick={onCreate} className="bg-emerald-500 hover:bg-emerald-500/90">
            <Plus className="h-4 w-4 mr-2" />
            Nouvelle catégorie
          </Button>
        )}
      </div>

      {/* État de chargement */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      )}

      {/* Liste vide */}
      {!isLoading && categories.length === 0 && (
        <div className="text-center py-12 rounded-2xl bg-white shadow-soft border border-[#E5E7EB]/50">
          <p className="text-[#6B7280]">
            {searchValue
              ? "Aucune catégorie trouvée pour cette recherche."
              : "Aucune catégorie créée pour le moment."}
          </p>
          {!searchValue && onCreate && (
            <Button onClick={onCreate} className="mt-4 bg-emerald-500 hover:bg-emerald-500/90">
              <Plus className="h-4 w-4 mr-2" />
              Créer votre première catégorie
            </Button>
          )}
        </div>
      )}

      {/* Grille de catégories */}
      {!isLoading && categories.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {categories.map((category) => (
            <CategoryCard
              key={category.id}
              category={category}
              onEdit={onEdit}
              onDelete={onDelete}
              onView={onView}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default CategoryList;
